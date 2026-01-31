import argparse
import time
import sys

# Import Strategy and Mock Client
from coi_strategy import COIBuyingStrategy
from mock_openalgo import MockOpenAlgoClient

def main():
    parser = argparse.ArgumentParser(description="COI Buying Strategy Executor")
    parser.add_argument("--mode", type=str, choices=["mock", "real"], default="mock", help="Execution mode")
    parser.add_argument("--apikey", type=str, default="test_key", help="OpenAlgo API Key")
    parser.add_argument("--host", type=str, default="http://127.0.0.1:5000", help="OpenAlgo Host URL")
    parser.add_argument("--symbol", type=str, default="NIFTY", help="Underlying Symbol")
    parser.add_argument("--expiry", type=str, default="28DEC23", help="Expiry Date (e.g., 28DEC23)")

    args = parser.parse_args()

    # Initialize Client
    if args.mode == "real":
        try:
            from openalgo import api
            client = api(api_key=args.apikey, host=args.host)
        except ImportError:
            print("Error: 'openalgo' library not installed. Please install it or use --mode mock")
            return
    else:
        print("Initializing Mock Client...")
        client = MockOpenAlgoClient(api_key=args.apikey, host=args.host)

    # Connect
    try:
        # client.connect() # Some implementations might need explicit connect
        pass
    except Exception as e:
        print(f"Connection warning: {e}")

    # Initialize Strategy
    strategy = COIBuyingStrategy(
        client=client,
        underlying=args.symbol,
        exchange="NSE_INDEX", # Assuming Index Options
        expiry_date=args.expiry,
        quantity=50
    )

    print(f"Starting Strategy Loop for {args.symbol} ({args.mode})...")

    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n--- Cycle {iteration} ---")

            # --- MOCK SIMULATION LOGIC ---
            if args.mode == "mock":
                # Cycle 2: Trigger a 500% Spike in PE at 25500 -> Should Buy ATM CE
                if iteration == 2:
                    client.set_spike(25500, "PE")

                # Cycle 5: Simulate Price Drop to Trigger SL (Entry was likely around 100)
                # If we bought CE, let's drop CE price.
                if iteration == 5 and strategy.active_trade and strategy.active_trade['status'] == 'OPEN':
                    # Force LTP to be below SL
                    sl_price = strategy.active_trade['sl']
                    client.set_ltp(sl_price - 5)

                # Cycle 8: Simulate Price Return to Entry (Re-entry condition)
                if iteration == 8 and strategy.active_trade and strategy.active_trade['status'] == 'WAITING_REENTRY':
                    entry_price = strategy.active_trade['entry_price']
                    client.set_ltp(entry_price + 1)

            # -----------------------------

            strategy.run_cycle()

            if args.mode == "mock" and iteration >= 10:
                print("Mock simulation finished.")
                break

            time.sleep(2) # Sleep between cycles

    except KeyboardInterrupt:
        print("\nStrategy stopped by user.")
    except Exception as e:
        print(f"\nCritical Error: {e}")

if __name__ == "__main__":
    main()
