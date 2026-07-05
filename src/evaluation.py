import vectorbt as vbt
import pandas as pd

def generate_tearsheet(portfolio, benchmark_close=None):
    print("--- Institutional Tearsheet ---")
    
    # Core Metrics
    stats = portfolio.stats()
    
    try:
        print(f"Total Return: {stats['Total Return [%]']:.2f}%")
        print(f"Max Drawdown: {stats['Max Drawdown [%]']:.2f}%")
        print(f"Calmar Ratio: {stats['Calmar Ratio']:.2f}")
        print(f"Sortino Ratio: {stats['Sortino Ratio']:.2f}")
        print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
    except KeyError as e:
        print(f"Key missing in stats: {e}")
        
    print("-" * 30)
    print("Full Stats:")
    print(stats)
    
    fig = portfolio.plot(subplots=['cum_returns', 'drawdowns', 'underwater'])
    
    # If benchmark is provided, add it to the cumulative returns plot
    if benchmark_close is not None:
        # Create a Buy and Hold portfolio for the benchmark
        bench_pf = vbt.Portfolio.from_holding(benchmark_close, init_cash=portfolio.init_cash)
        
        # We need to extract the trace from bench_pf.plot_cum_returns() and add it to fig
        bench_returns = bench_pf.cumulative_returns() * 100 # vbt usually plots returns as percentage or multiplier
        fig.add_scatter(
            x=bench_returns.index,
            y=bench_returns.values,
            mode='lines',
            name="Benchmark (Buy & Hold Nifty)",
            row=1, col=1
        )
        
    return fig
