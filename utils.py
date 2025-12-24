import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import pulp
from datetime import datetime, timedelta


def calculate_demand(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate demand by aggregating orders by Origin and Product_Category.
    
    Args:
        orders: DataFrame with Order_ID, Order_Date, Origin, Product_Category, Order_Value_INR
        
    Returns:
        DataFrame with Origin, Product_Category, Monthly_Demand
    """
    orders['Order_Date'] = pd.to_datetime(orders['Order_Date'])
    
    # Group by Origin and Product_Category to get demand
    demand = orders.groupby(['Origin', 'Product_Category']).size().reset_index(name='Monthly_Demand')
    
    return demand


def compute_spi(warehouse: pd.DataFrame, demand: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Stock Pressure Index (SPI) for each warehouse-product combination.
    
    SPI = (Current_Stock_Units - Reorder_Level) - Predicted_Demand
    
    Args:
        warehouse: DataFrame with warehouse inventory data
        demand: DataFrame with demand data
        
    Returns:
        DataFrame with SPI calculations
    """
    # Merge warehouse and demand data
    merged = warehouse.merge(
        demand,
        left_on=['Location', 'Product_Category'],
        right_on=['Origin', 'Product_Category'],
        how='left'
    )
    
    # Fill missing demand with 0
    merged = merged.copy()
    merged['Monthly_Demand'] = merged['Monthly_Demand'].fillna(0)
    
    # Calculate SPI
    merged['SPI'] = (merged['Current_Stock_Units'] - merged['Reorder_Level']) - merged['Monthly_Demand']
    
    return merged


def recommend_transfers(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Generate transfer recommendations between warehouses based on SPI.
    
    Args:
        merged: DataFrame with SPI calculations
        
    Returns:
        DataFrame with transfer recommendations
    """
    shortages = merged[merged['SPI'] < 0].copy()
    surplus = merged[merged['SPI'] > 0].copy()
    
    recommendations = []
    
    for _, row in shortages.iterrows():
        # Find surplus warehouses with same product category
        same_cat = surplus[surplus['Product_Category'] == row['Product_Category']]
        
        if not same_cat.empty:
            # Select the warehouse with highest surplus
            donor = same_cat.sort_values('SPI', ascending=False).iloc[0]
            
            # Calculate transfer units
            units = min(abs(row['SPI']), donor['SPI'])
            
            # Calculate cost savings
            savings = units * (donor['Storage_Cost_per_Unit'] - row['Storage_Cost_per_Unit'])
            
            recommendations.append({
                'Product_Category': row['Product_Category'],
                'From_Warehouse': donor['Warehouse_ID'],
                'From_Location': donor['Location'],
                'To_Warehouse': row['Warehouse_ID'],
                'To_Location': row['Location'],
                'Units': int(units),
                'Estimated_Saving_INR': round(savings, 2),
                'Donor_SPI': round(donor['SPI'], 2),
                'Receiver_SPI': round(row['SPI'], 2)
            })
    
    return pd.DataFrame(recommendations)


def optimize_transfers(merged: pd.DataFrame, distance_matrix: Dict = None) -> pd.DataFrame:
    """
    Use linear optimization to find optimal transfer plan.
    
    Args:
        merged: DataFrame with SPI calculations
        distance_matrix: Optional distance matrix between locations
        
    Returns:
        DataFrame with optimized transfer recommendations
    """
    # For now, use the simple recommendation logic
    # In a full implementation, this would use PuLP for optimization
    return recommend_transfers(merged)


def calculate_metrics(merged: pd.DataFrame) -> Dict:
    """
    Calculate key business metrics.
    
    Args:
        merged: DataFrame with SPI calculations
        
    Returns:
        Dictionary with key metrics
    """
    total_shortages = len(merged[merged['SPI'] < 0])
    total_warehouses = merged['Warehouse_ID'].nunique()
    total_skus = len(merged)
    avg_spi = merged['SPI'].mean()
    
    # Calculate potential cost savings
    recommendations = recommend_transfers(merged)
    total_savings = recommendations['Estimated_Saving_INR'].sum() if not recommendations.empty else 0
    
    # Find top risk categories
    risk_categories = merged.groupby('Product_Category')['SPI'].min().sort_values().head(3)
    
    return {
        'total_warehouses': total_warehouses,
        'total_skus': total_skus,
        'shortage_percentage': round((total_shortages / total_skus) * 100, 2),
        'average_spi': round(avg_spi, 2),
        'potential_cost_saving': round(total_savings, 2),
        'top_risk_categories': risk_categories.to_dict()
    }


def simulate_demand_change(orders: pd.DataFrame, demand_change_pct: float) -> pd.DataFrame:
    """
    Simulate demand changes for what-if analysis.
    
    Args:
        orders: Original orders DataFrame
        demand_change_pct: Percentage change in demand (e.g., 0.1 for 10% increase)
        
    Returns:
        Modified orders DataFrame
    """
    orders_sim = orders.copy()
    
    # Simulate demand change by adjusting order frequency
    if demand_change_pct != 0:
        # Create additional or remove orders based on percentage
        num_orders = len(orders_sim)
        change_amount = int(num_orders * abs(demand_change_pct))
        
        if demand_change_pct > 0:
            # Increase demand by duplicating some orders
            additional_orders = orders_sim.sample(n=min(change_amount, num_orders), replace=True)
            orders_sim = pd.concat([orders_sim, additional_orders], ignore_index=True)
        else:
            # Decrease demand by removing some orders
            orders_sim = orders_sim.sample(n=max(num_orders - change_amount, 1))
    
    return orders_sim


def simulate_cost_change(warehouse: pd.DataFrame, cost_change_pct: float) -> pd.DataFrame:
    """
    Simulate storage cost changes for what-if analysis.
    
    Args:
        warehouse: Original warehouse DataFrame
        cost_change_pct: Percentage change in storage costs
        
    Returns:
        Modified warehouse DataFrame
    """
    warehouse_sim = warehouse.copy()
    
    if cost_change_pct != 0:
        warehouse_sim['Storage_Cost_per_Unit'] = warehouse_sim['Storage_Cost_per_Unit'] * (1 + cost_change_pct)
    
    return warehouse_sim


def validate_data(warehouse: pd.DataFrame, orders: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate input data for required columns and data quality.
    
    Args:
        warehouse: Warehouse inventory DataFrame
        orders: Orders DataFrame
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check warehouse data
    required_warehouse_cols = ['Warehouse_ID', 'Location', 'Product_Category', 
                              'Current_Stock_Units', 'Reorder_Level', 'Storage_Cost_per_Unit']
    missing_warehouse_cols = [col for col in required_warehouse_cols if col not in warehouse.columns]
    if missing_warehouse_cols:
        errors.append(f"Missing warehouse columns: {missing_warehouse_cols}")
    
    # Check orders data
    required_orders_cols = ['Order_ID', 'Order_Date', 'Origin', 'Product_Category', 'Order_Value_INR']
    missing_orders_cols = [col for col in required_orders_cols if col not in orders.columns]
    if missing_orders_cols:
        errors.append(f"Missing orders columns: {missing_orders_cols}")
    
    # Check for negative stock or costs
    if 'Current_Stock_Units' in warehouse.columns:
        if (warehouse['Current_Stock_Units'] < 0).any():
            errors.append("Negative stock units found in warehouse data")
    
    if 'Storage_Cost_per_Unit' in warehouse.columns:
        if (warehouse['Storage_Cost_per_Unit'] < 0).any():
            errors.append("Negative storage costs found in warehouse data")
    
    return len(errors) == 0, errors
