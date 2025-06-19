"""
Flight Price Comparison and Time Series Analysis

This module provides functionality for comparing flight prices across different 
time periods and analyzing competitive pricing dynamics.

Date: June 18, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
from pathlib import Path
import argparse

class FlightPriceComparator:
    """
    A class for comparing flight prices across different time periods
    and analyzing competitive pricing dynamics.
    """
    
    def __init__(self, snapshots_dir="snapshots"):
        """
        Initialize the price comparator.
        
        Args:
            snapshots_dir (str): Directory containing snapshot subdirectories
        """
        self.snapshots_dir = Path(snapshots_dir)
        self.results_dir = Path("analysis_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def load_snapshot(self, date_str):
        """
        Load a specific snapshot by date.
        
        Args:
            date_str (str): Date in YYYYMMDD format
            
        Returns:
            pd.DataFrame: Flight price data for the specified date
        """
        snapshot_path = self.snapshots_dir / date_str / "all_routes.csv"
        
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
            
        df = pd.read_csv(snapshot_path)
        df['snapshot_date'] = date_str
        return df
        
    def compare_snapshots(self, date1, date2):
        """
        Compare two snapshots and calculate price differences. (right now only for two dates)
        
        Args:
            date1 (str): Earlier date in YYYYMMDD format
            date2 (str): Later date in YYYYMMDD format
            
        Returns:
            pd.DataFrame: Merged dataframe with price comparison metrics
        """
        print(f"📊 Comparing snapshots: {date1} vs {date2}")
        
        # Load both snapshots
        df1 = self.load_snapshot(date1)
        df2 = self.load_snapshot(date2)
        
        print(f"   • {date1}: {len(df1)} records")
        print(f"   • {date2}: {len(df2)} records")
        
        # Create matching keys for comparison
        merge_cols = ['origin', 'destination', 'depart_date', 'gate']
        
        # Merge on common flights
        merged = pd.merge(
            df2[merge_cols + ['price_eur']],
            df1[merge_cols + ['price_eur']],
            on=merge_cols,
            suffixes=('_new', '_old'),
            how='inner'
        )
        
        # Calculate price changes
        merged['price_diff'] = merged['price_eur_new'] - merged['price_eur_old']
        merged['change_pct'] = (merged['price_diff'] / merged['price_eur_old']) * 100
        merged['route'] = merged['origin'] + ' → ' + merged['destination']
        
        # Categorize changes
        merged['change_type'] = pd.cut(
            merged['change_pct'],
            bins=[-float('inf'), -5, -1, 1, 5, float('inf')],
            labels=['Major Drop (>5%)', 'Minor Drop (1-5%)', 'Stable (±1%)', 
                   'Minor Increase (1-5%)', 'Major Increase (>5%)']
        )
        
        print(f"   • Matched flights: {len(merged)}")
        print(f"   • Changed prices: {len(merged[merged['price_diff'] != 0])}")
        
        return merged
        
    def analyze_ota_changes(self, comparison_df):
        """
        Analyze price changes by OTA.
        
        Args:
            comparison_df (pd.DataFrame): Result from compare_snapshots()
            
        Returns:
            pd.DataFrame: OTA-level price change analysis
        """
        ota_analysis = comparison_df.groupby('gate').agg({
            'price_diff': ['count', 'mean', 'std'],
            'change_pct': ['mean', 'min', 'max'],
            'price_eur_new': 'mean'
        }).round(2)
        
        # Flatten column names
        ota_analysis.columns = [
            'total_flights', 'avg_price_diff', 'std_price_diff',
            'avg_change_pct', 'min_change_pct', 'max_change_pct', 'avg_current_price'
        ]
        
        # Add strategy classification
        ota_analysis['pricing_strategy'] = ota_analysis['avg_change_pct'].apply(
            lambda x: 'Aggressive Increase' if x > 5 
                     else 'Moderate Increase' if x > 1
                     else 'Stable' if abs(x) <= 1
                     else 'Moderate Decrease' if x > -5
                     else 'Aggressive Decrease'
        )
        
        return ota_analysis.sort_values('avg_change_pct', ascending=False)
        
    def analyze_route_changes(self, comparison_df):
        """
        Analyze price changes by route.
        
        Args:
            comparison_df (pd.DataFrame): Result from compare_snapshots()
            
        Returns:
            pd.DataFrame: Route-level price change analysis
        """
        route_analysis = comparison_df.groupby('route').agg({
            'price_diff': ['count', 'mean', 'std'],
            'change_pct': ['mean', 'min', 'max'],
            'gate': 'nunique'
        }).round(2)
        
        # Flatten column names
        route_analysis.columns = [
            'total_flights', 'avg_price_diff', 'std_price_diff',
            'avg_change_pct', 'min_change_pct', 'max_change_pct', 'num_otas'
        ]
        
        return route_analysis.sort_values('avg_change_pct', ascending=False)
        
    def create_comparison_visualizations(self, comparison_df, date1, date2):
        """
        Create comprehensive visualizations for price comparison analysis.
        
        Args:
            comparison_df (pd.DataFrame): Result from compare_snapshots()
            date1 (str): Earlier date
            date2 (str): Later date
        """
        # Set up the plotting style with improved font settings
        plt.style.use('seaborn-v0_8')
        plt.rcParams.update({
            'font.size': 12,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'font.family': 'DejaVu Sans'  # For emojis
        })        
        fig = plt.figure(figsize=(24, 18), constrained_layout=False)
        gs = fig.add_gridspec(3, 3, width_ratios=[1, 1, 1], hspace=0.4, wspace=0.3)
          # 1. Price Change Distribution
        ax1 = plt.subplot(gs[0, 0])
        comparison_df['change_pct'].hist(bins=50, alpha=0.7, color='steelblue')
        ax1.axvline(0, color='red', linestyle='--', alpha=0.7)
        ax1.set_title(f'Price Change Distribution\n{date1} → {date2}', fontweight='bold')
        ax1.set_xlabel('Price Change (%)')
        ax1.set_ylabel('Frequency')        # 2. Change Type Distribution
        ax2 = plt.subplot(gs[0, 1])
        change_counts = comparison_df['change_type'].value_counts()
        
        # Calculate percentages and create labels with percentages
        percentages = (change_counts / change_counts.sum() * 100).round(1)
        labels = [f"{cat} – {pct}%" for cat, pct in zip(change_counts.index, percentages)]
        
        colors = ['red', 'orange', 'gray', 'lightgreen', 'green']
          # Pie chart 
        ax2.pie(change_counts.values, labels=None, colors=colors, startangle=90, 
                textprops={'fontsize': 9})        
        ax2.legend(labels, loc='center right', bbox_to_anchor=(-0.25, 0.5), 
                  bbox_transform=ax2.transAxes, fontsize=8, frameon=False)
        ax2.set_title('Change Type Distribution', fontweight='bold')
        
        # 3. OTA Average Change
        ax3 = plt.subplot(gs[0, 2])
        ota_avg = comparison_df.groupby('gate')['change_pct'].mean().sort_values()
        bars = ax3.barh(range(len(ota_avg)), ota_avg.values, 
                       color=['red' if x < 0 else 'green' for x in ota_avg.values])
        ax3.set_yticks(range(len(ota_avg)))
        ax3.set_yticklabels(ota_avg.index)
        ax3.set_title('Average Price Change by OTA', fontweight='bold')
        ax3.set_xlabel('Average Change (%)')
        ax3.axvline(0, color='black', linestyle='-', alpha=0.3)
          # 4. Route Average Change
        ax4 = plt.subplot(gs[1, 0])
        route_avg = comparison_df.groupby('route')['change_pct'].mean().sort_values()
        ax4.barh(range(len(route_avg)), route_avg.values,
                color=['red' if x < 0 else 'green' for x in route_avg.values])
        ax4.set_yticks(range(len(route_avg)))
        ax4.set_yticklabels(route_avg.index, fontsize=7)  
        ax4.set_title('Average Price Change by Route', fontweight='bold')
        ax4.set_xlabel('Average Change (%)')
        ax4.axvline(0, color='black', linestyle='-', alpha=0.3)
        
        # 5. Price vs Change Scatter
        ax5 = plt.subplot(gs[1, 1])
        scatter = ax5.scatter(comparison_df['price_eur_old'], comparison_df['change_pct'], 
                            alpha=0.6, c=comparison_df['change_pct'], cmap='RdYlGn_r')
        ax5.set_xlabel('Original Price (€)')
        ax5.set_ylabel('Price Change (%)')
        ax5.set_title('Price vs Change Relationship', fontweight='bold')
        plt.colorbar(scatter, ax=ax5)
          # 6. Biggest Price Increases
        ax6 = plt.subplot(gs[1, 2])
        biggest_increases = comparison_df.nlargest(10, 'price_diff')
        ax6.barh(range(len(biggest_increases)), biggest_increases['price_diff'], color='red', alpha=0.7)
        ax6.set_yticks(range(len(biggest_increases)))
        ax6.set_yticklabels([f"{row['gate']}: {row['route']}" for _, row in biggest_increases.iterrows()], fontsize=7)
        ax6.set_title('Biggest Price Increases (EUR)', fontweight='bold')
        ax6.set_xlabel('Price Increase (€)')
        
        # 7. Biggest Price Decreases
        ax7 = plt.subplot(gs[2, 0])
        biggest_decreases = comparison_df.nsmallest(10, 'price_diff')
        ax7.barh(range(len(biggest_decreases)), biggest_decreases['price_diff'], color='green', alpha=0.7)
        ax7.set_yticks(range(len(biggest_decreases)))
        ax7.set_yticklabels([f"{row['gate']}: {row['route']}" for _, row in biggest_decreases.iterrows()], fontsize=7)
        ax7.set_title('Biggest Price Decreases (EUR)', fontweight='bold')
        ax7.set_xlabel('Price Decrease (€)')        # 8. OTA Market Share
        ax8 = plt.subplot(gs[2, 1])
        ota_share = comparison_df['gate'].value_counts()
        
        # Calculate percentages and create labels with percentages
        percent_ota = (ota_share / ota_share.sum() * 100).round(1)
        labels_ota = [f"{ota} – {pct}%" for ota, pct in zip(ota_share.index, percent_ota)]
          # Pie chart 2
        ax8.pie(ota_share.values, labels=None, startangle=90, textprops={'fontsize': 9})       
        ax8.legend(labels_ota, loc='center right', bbox_to_anchor=(-0.25, 0.5), 
                  bbox_transform=ax8.transAxes, fontsize=8, frameon=False)
        ax8.set_title('OTA Market Share in Analysis', fontweight='bold')
          # 9. Summary Statistics
        ax9 = plt.subplot(gs[2, 2])
        ax9.axis('off')
        
        # Calculate summary stats
        total_flights = len(comparison_df)
        changed_flights = len(comparison_df[comparison_df['price_diff'] != 0])
        avg_change = comparison_df['change_pct'].mean()
        max_increase = comparison_df['price_diff'].max()
        max_decrease = comparison_df['price_diff'].min()
        
        summary_text = f"""
ANALYSIS SUMMARY
{date1} → {date2}

Total Flights Analyzed: {total_flights:,}
Flights with Price Changes: {changed_flights:,} ({changed_flights/total_flights*100:.1f}%)
Average Price Change: {avg_change:.2f}%
Biggest Increase: €{max_increase:.2f}
Biggest Decrease: €{max_decrease:.2f}

Active OTAs: {comparison_df['gate'].nunique()}
Routes Monitored: {comparison_df['route'].nunique()}        """
        
        ax9.text(0.1, 0.9, summary_text, transform=ax9.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))        
        # Adjust subplot spacing
        plt.subplots_adjust(left=0.05, bottom=0.05, right=0.96, top=0.95, 
                           wspace=0.35, hspace=0.45)  
        
        # Save the visualization with higher DPI
        filename = f"price_comparison_{date1}_to_{date2}.png"
        filepath = self.results_dir / filename
        plt.savefig(filepath, dpi=400, bbox_inches='tight')  
        print(f"📊 Visualization saved: {filepath}")
        
        plt.show()
        
    def generate_comparison_report(self, date1, date2):
        """
        Generate a comprehensive comparison report between two dates. Right now only for only two dates. 
        
        Args:
            date1 (str): Earlier date in YYYYMMDD format
            date2 (str): Later date in YYYYMMDD format
        """
        print(f"\n🚀 Generating Comprehensive Price Comparison Report")
        print(f"📅 Period: {date1} → {date2}")
        print("=" * 60)
        
        # Perform comparison
        comparison_df = self.compare_snapshots(date1, date2)
        
        # Analyze by OTA
        print(f"\n🏢 OTA PRICING STRATEGY ANALYSIS:")
        print("-" * 40)
        ota_analysis = self.analyze_ota_changes(comparison_df)
        print(ota_analysis)
        
        # Analyze by Route
        print(f"\n✈️ ROUTE PRICING TREND ANALYSIS:")
        print("-" * 40)
        route_analysis = self.analyze_route_changes(comparison_df)
        print(route_analysis)
        
        # Generate visualizations
        print(f"\n📊 CREATING VISUALIZATIONS...")
        print("-" * 40)
        self.create_comparison_visualizations(comparison_df, date1, date2)
        
        # Save detailed results
        results_filename = f"detailed_comparison_{date1}_to_{date2}.csv"
        results_path = self.results_dir / results_filename
        comparison_df.to_csv(results_path, index=False)
        print(f"💾 Detailed results saved: {results_path}")
        
        # Save OTA analysis
        ota_filename = f"ota_analysis_{date1}_to_{date2}.csv"
        ota_path = self.results_dir / ota_filename
        ota_analysis.to_csv(ota_path)
        print(f"🏢 OTA analysis saved: {ota_path}")
        
        # Save route analysis
        route_filename = f"route_analysis_{date1}_to_{date2}.csv"
        route_path = self.results_dir / route_filename
        route_analysis.to_csv(route_path)
        print(f"✈️ Route analysis saved: {route_path}")
        
        print(f"\n✅ Comparison report completed successfully!")
        return comparison_df, ota_analysis, route_analysis


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description='Flight Price Comparison Analysis')
    parser.add_argument('--date1', required=True, help='Earlier date (YYYYMMDD)')
    parser.add_argument('--date2', required=True, help='Later date (YYYYMMDD)')
    parser.add_argument('--snapshots-dir', default='snapshots', help='Snapshots directory')
    
    args = parser.parse_args()
    
    # Initialize comparator
    comparator = FlightPriceComparator(args.snapshots_dir)
    
    # Generate report
    comparator.generate_comparison_report(args.date1, args.date2)


if __name__ == "__main__":
    main()
