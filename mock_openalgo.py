import time
import random

class MockOpenAlgoClient:
    """
    A mock client that mimics the interface of the openalgo.api client
    for testing the COI Buying Strategy.
    """
    def __init__(self, api_key=None, host=None, ws_url=None):
        self.api_key = api_key
        self.host = host
        self.orders = []
        # Simulation state
        self.current_ltp = 25500.0
        self.spike_strike = 25500  # Strike where we simulate the spike
        self.spike_type = "PE"     # "CE" or "PE"
        self.triggered_spike = False

    def connect(self):
        print("[MockClient] Connected.")

    def disconnect(self):
        print("[MockClient] Disconnected.")

    def optionchain(self, underlying, exchange, expiry_date, strike_count=10):
        """
        Returns a mocked option chain.
        We will simulate a 500% spike in OI for the ATM strike.
        """
        print(f"[MockClient] Fetching option chain for {underlying} {expiry_date}...")

        atm = self.current_ltp
        # Round to nearest 50
        atm_strike = round(atm / 50) * 50

        chain_data = []

        # Generate strikes around ATM
        for i in range(-5, 6):
            strike = atm_strike + (i * 50)

            # Base OI
            ce_oi = 10000
            pe_oi = 10000
            ce_change_oi = 0
            pe_change_oi = 0

            # Simulate a Massive Spike if configured
            if strike == self.spike_strike and self.triggered_spike:
                if self.spike_type == "PE":
                    pe_oi = 62000  # > 500% increase from base 10000
                    pe_change_oi = 52000
                elif self.spike_type == "CE":
                    ce_oi = 62000
                    ce_change_oi = 52000

            # Construct CE/PE objects (simplified version of API response)
            ce_data = {
                "symbol": f"{underlying}{expiry_date}{strike}CE",
                "ltp": max(1.0, 100 - i*10 + random.uniform(-1, 1)),
                "oi": ce_oi,
                "oichange": ce_change_oi, # Note: API docs didn't explicitly show 'oichange' in the 'chain' list example,
                                          # but usually it's derived or present. We'll compute % change manually in strategy if needed,
                                          # but let's assume we use raw OI to calculate change from previous snapshot
                                          # OR the API provides it. The docs showed 'oi'.
                                          # Strategy will likely need to track 'previous OI' to calculate % change
                                          # if the API doesn't provide 'changeinOpenInterest'.
                                          # Wait, the CSV provided in the task had 'changeinOpenInterest'.
                                          # The OpenAlgo API docs example for 'optionchain' showed 'oi' but not explicitly 'change_oi'.
                                          # I will assume for the mock that we return 'oi' and the strategy calculates change
                                          # based on *previous* tick, OR I mock 'oi' such that it *looks* like a change.
                                          # *Correction*: The user requirements say "Calculate the real-time % Change in OI".
                                          # This implies I might need to fetch data twice or maintain history.
                                          # However, usually Option Chain data *includes* "Change in OI".
                                          # Let's add 'change_oi' to the mock for completeness, even if I have to calculate it in the strategy.
                "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0
            }

            pe_data = {
                "symbol": f"{underlying}{expiry_date}{strike}PE",
                "ltp": max(1.0, 100 + i*10 + random.uniform(-1, 1)),
                "oi": pe_oi,
                "oichange": pe_change_oi,
                "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0
            }

            chain_data.append({
                "strike": strike,
                "ce": ce_data,
                "pe": pe_data
            })

        return {
            "status": "success",
            "underlying": underlying,
            "expiry_date": expiry_date,
            "atm_strike": atm_strike,
            "chain": chain_data
        }

    def optionsorder(self, strategy, underlying, exchange, expiry_date, offset, option_type, action, quantity, pricetype="MARKET", product="NRML", splitsize=0):
        print(f"[MockClient] Placing Order: {action} {quantity} {underlying} {offset} {option_type}")

        # Mock Response
        order_id = int(time.time() * 1000)

        # Determine symbol name for response
        symbol = f"{underlying}{expiry_date}{offset}{option_type}" # Simplified

        return {
            "status": "success",
            "orderid": str(order_id),
            "symbol": symbol,
            "exchange": "NFO",
            "underlying": underlying,
            "offset": offset,
            "option_type": option_type
        }

    def placeorder(self, strategy, symbol, action, exchange, price_type="MARKET", product="MIS", quantity=1, price=0, trigger_price=0, disclosed_quantity=0):
        """
        Mock for placing standard orders (e.g., closing positions).
        """
        print(f"[MockClient] Placing Standard Order: {action} {quantity} {symbol} ({price_type})")
        return {
            "status": "success",
            "orderid": str(int(time.time() * 1000))
        }

    def quotes(self, symbol, exchange):
        # Return a dummy quote for LTP monitoring
        return {
            "status": "success",
            "data": {
                "ltp": self.current_ltp,
                "symbol": symbol,
                "exchange": exchange
            }
        }

    # Helper to set the mock state
    def set_spike(self, strike, otype):
        self.triggered_spike = True
        self.spike_strike = strike
        self.spike_type = otype
        print(f"[MockClient] Simulating 500% spike in {otype} at {strike}")

    def set_ltp(self, price):
        self.current_ltp = price
        print(f"[MockClient] Underlying LTP set to {price}")
