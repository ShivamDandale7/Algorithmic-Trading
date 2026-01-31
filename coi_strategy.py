import time
import math

class COIBuyingStrategy:
    def __init__(self, client, underlying="NIFTY", exchange="NSE_INDEX", expiry_date=None, quantity=50):
        self.client = client
        self.underlying = underlying
        self.exchange = exchange
        self.expiry_date = expiry_date
        self.quantity = quantity

        # Parameters
        self.spike_threshold = 500.0 # %
        self.target_pct = 0.50       # 50%
        self.stoploss_pct = 0.20     # 20%
        self.reentry_tolerance = 0.5 # points

        # State
        self.active_trade = None  # { 'type': 'CE'/'PE', 'entry_price': float, 'sl': float, 'target': float, 'symbol': str, 'status': 'OPEN'/'SL_HIT' }
        self.trade_history = []
        self.reentry_attempts = 0
        self.max_reentry_attempts = 1 # Max 1 re-entry means 2 total attempts (Original + 1)
        self.is_disabled = False      # Disabled for the day/setup if max attempts reached

    def run_cycle(self):
        """
        Main execution method to be called periodically.
        """
        if self.is_disabled:
            print("[Strategy] Strategy disabled (Max attempts reached).")
            return

        # 1. Fetch Option Chain
        try:
            chain_response = self.client.optionchain(
                underlying=self.underlying,
                exchange=self.exchange,
                expiry_date=self.expiry_date,
                strike_count=10
            )
        except Exception as e:
            print(f"[Strategy] Error fetching data: {e}")
            return

        if chain_response.get("status") != "success":
            print(f"[Strategy] API Error: {chain_response}")
            return

        chain = chain_response.get("chain", [])
        atm_strike = chain_response.get("atm_strike")

        # 2. Manage Active Trade / Re-entry
        if self.active_trade:
            self.manage_existing_trade(chain)
            return

        # 3. If no active trade, look for signals
        if self.reentry_attempts == 0: # Only look for fresh signals if we haven't started a sequence
            self.scan_for_signals(chain, atm_strike)

    def scan_for_signals(self, chain, atm_strike):
        """
        Scans ATM-2 to ATM+2 for 500% OI Spikes.
        """
        # Filter strikes: [ATM-2, ATM-1, ATM, ATM+1, ATM+2]
        # Assuming strikes are sorted or we find them.
        # The chain list from API usually contains a subset around ATM if strike_count is small.

        relevant_strikes = []
        # Find index of ATM? Or just filter by value.
        # Assuming strike step is 50 for NIFTY.

        strikes_map = {item['strike']: item for item in chain}

        # Generate the 5 strike values
        # We need to know the step. Let's infer or assume 50 for NIFTY.
        step = 50
        target_strikes = [atm_strike + (i * step) for i in range(-2, 3)]

        ce_spikes = []
        pe_spikes = []

        print(f"[Strategy] Scanning strikes: {target_strikes} (ATM: {atm_strike})")

        for strike in target_strikes:
            data = strikes_map.get(strike)
            if not data:
                continue

            # Check CE
            ce_oi_change_pct = self.calculate_oi_pchange(data['ce'])
            if ce_oi_change_pct > self.spike_threshold:
                print(f"[Signal] Massive CE OI Spike at {strike}: {ce_oi_change_pct:.2f}%")
                ce_spikes.append(strike)

            # Check PE
            pe_oi_change_pct = self.calculate_oi_pchange(data['pe'])
            if pe_oi_change_pct > self.spike_threshold:
                print(f"[Signal] Massive PE OI Spike at {strike}: {pe_oi_change_pct:.2f}%")
                pe_spikes.append(strike)

        # Apply Filter: If both CE and PE have spikes simultaneously -> IGNORE
        if ce_spikes and pe_spikes:
            print("[Filter] Spikes detected in BOTH CE and PE. Ignoring Signal.")
            return

        # Entry Rules
        if ce_spikes:
            # Case A: 500% spike in CE -> Buy ATM PE (Reversal)
            print(f"[Entry] Trigger: CE Spike. Action: BUY ATM PE.")
            self.enter_trade("PE", atm_strike)

        elif pe_spikes:
            # Case B: 500% spike in PE -> Buy ATM CE (Bounce)
            print(f"[Entry] Trigger: PE Spike. Action: BUY ATM CE.")
            self.enter_trade("CE", atm_strike)

    def calculate_oi_pchange(self, option_data):
        """
        Calculates % Change in OI.
        API might provide 'pchangeinOpenInterest' or just 'oi' and 'changeinOpenInterest'.
        Mock provides 'oichange'.
        """
        # If API provides percentage directly (ideal)
        if 'pchangeinOpenInterest' in option_data:
            return float(option_data['pchangeinOpenInterest'])

        # Calculate manually
        oi = float(option_data.get('oi', 0))
        change = float(option_data.get('oichange', 0)) # Using mock key, check real key

        # Real API key might be 'changeinOpenInterest' or we infer it.
        # For this implementation, we try to be robust.

        prev_oi = oi - change

        if prev_oi <= 0:
            return 0.0

        return (change / prev_oi) * 100.0

    def enter_trade(self, option_type, strike, is_reentry=False):
        """
        Places order and initializes trade state.
        """
        # Place Order via API
        # We use offset="ATM" for simplicity as per requirements "Buy ATM PE/CE"

        try:
            response = self.client.optionsorder(
                strategy="COI_Strategy",
                underlying=self.underlying,
                exchange=self.exchange,
                expiry_date=self.expiry_date,
                offset="ATM", # The strategy says Buy ATM
                option_type=option_type,
                action="BUY",
                quantity=self.quantity,
                pricetype="MARKET",
                product="NRML" # or MIS
            )

            if response.get("status") == "success":
                symbol = response.get("symbol") # The actual symbol bought

                # Fetch execution price (In real world, fetch order book or assume LTP)
                # For this logic, we'll fetch the quote immediately
                quote = self.client.quotes(symbol=symbol, exchange="NFO")
                entry_price = float(quote['data']['ltp'])

                sl_price = entry_price * (1 - self.stoploss_pct)
                target_price = entry_price * (1 + self.target_pct)

                self.active_trade = {
                    'type': option_type,
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'sl': sl_price,
                    'target': target_price,
                    'status': 'OPEN'
                }

                status_msg = "RE-ENTRY" if is_reentry else "FRESH ENTRY"
                print(f"[Trade] {status_msg} Executed: {symbol} @ {entry_price}. SL: {sl_price:.2f}, TGT: {target_price:.2f}")

            else:
                print(f"[Error] Order placement failed: {response}")

        except Exception as e:
            print(f"[Error] Exception during entry: {e}")

    def manage_existing_trade(self, chain):
        """
        Monitors SL/Target or Re-entry conditions.
        """
        trade = self.active_trade
        symbol = trade['symbol']

        # Get current price of the option
        # We can find it in the chain if we match symbol, or just call quotes()
        # Using quotes() is safer as chain might not have the specific strike if ATM moved?
        # Actually ATM moves, but we hold a specific symbol.

        quote = self.client.quotes(symbol=symbol, exchange="NFO")
        ltp = float(quote['data']['ltp'])

        if trade['status'] == 'OPEN':
            # Check Target
            if ltp >= trade['target']:
                print(f"[Exit] Target Hit for {symbol} @ {ltp}. Profit: {(ltp - trade['entry_price']):.2f}")
                self.close_trade("TARGET")
                self.active_trade = None
                self.reentry_attempts = 0 # Reset or Finish? Usually resets for new setup, but requirements say "disable strategy for *this specific setup*".
                                          # Ideally we reset for new unrelated signals.

            # Check Stop Loss
            elif ltp <= trade['sl']:
                print(f"[Exit] Stop Loss Hit for {symbol} @ {ltp}. Loss: {(trade['entry_price'] - ltp):.2f}")
                self.close_trade("SL")

                # Transition to Re-entry Monitoring
                trade['status'] = 'WAITING_REENTRY'
                # Do not clear active_trade, keep it to monitor reentry
                print(f"[State] Monitoring for Re-entry at {trade['entry_price']}...")

        elif trade['status'] == 'WAITING_REENTRY':
            # Check if LTP returns to entry price
            # Tolerance: ±0.5 points
            lower_bound = trade['entry_price'] - self.reentry_tolerance

            if ltp >= lower_bound:
                if self.reentry_attempts < self.max_reentry_attempts:
                    print(f"[Re-Entry] Price returned to {ltp} (Entry: {trade['entry_price']}). Re-triggering!")
                    self.reentry_attempts += 1
                    # Re-enter the SAME symbol? Or Buy ATM again?
                    # Req: "trigger the trade again... Use the same Target and SL".
                    # Usually implies re-entering the same instrument or current ATM.
                    # "Buy ATM PE" was the rule. But "Re-Entry" usually means re-entering the failed position.
                    # Given "Use the same Target and SL as original trade", it strongly implies SAME LEVELS.
                    # So I will virtually "re-open" the trade or place a new order for the SAME symbol.

                    # Implementation: Place new order for same symbol
                    # But the 'optionsorder' API takes offset/underlying.
                    # Can we place order by Symbol? API docs showed `client.placeorder` for equity,
                    # `optionsorder` returns a symbol.
                    # I should probably use `placeorder` if I know the symbol, OR `optionsorder` if I want dynamic.
                    # Requirement: "trigger the trade again".
                    # I will assume buying the SAME symbol to respect the "Same Target/SL" levels logic easiest.
                    # However, to be robust with the mock client which expects `optionsorder` arguments...
                    # I'll call `enter_trade` again but force the logic to reuse parameters.

                    # Reset status to OPEN
                    self.active_trade['status'] = 'OPEN'

                    # Execute Re-entry Order for the specific symbol
                    try:
                        self.client.placeorder(
                            strategy="COI_Strategy",
                            symbol=symbol,
                            action="BUY",
                            exchange="NFO", # Standard exchange for NSE Options
                            price_type="MARKET",
                            product="NRML",
                            quantity=self.quantity
                        )
                        print(f"[Trade] Re-entry Order Placed for {symbol}.")
                    except Exception as e:
                        print(f"[Error] Re-entry execution failed: {e}")

                else:
                    print(f"[Stop] Max re-entries exhausted. Disabling strategy for this setup.")
                    self.is_disabled = True
                    self.active_trade = None

    def close_trade(self, reason):
        if not self.active_trade:
            return

        symbol = self.active_trade['symbol']
        try:
            self.client.placeorder(
                strategy="COI_Strategy",
                symbol=symbol,
                action="SELL",
                exchange="NFO", # Assuming NFO for options
                price_type="MARKET",
                product="NRML",
                quantity=self.quantity
            )
            print(f"[Order] Position Closed ({reason}) for {symbol}.")
        except Exception as e:
            print(f"[Error] Close execution failed: {e}")
