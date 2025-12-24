import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from utils import (
    calculate_demand, compute_spi, recommend_transfers, 
    calculate_metrics, simulate_demand_change, simulate_cost_change,
    validate_data
)

# Page configuration
st.set_page_config(
    page_title="Warehouse Inventory Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 300;
        letter-spacing: 1px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .warning-card {
        background-color: #fff8e1;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #f39c12;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-card {
        background-color: #e8f5e8;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #27ae60;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f8f9fa;
        border-radius: 4px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3498db;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_sample_data():
    """Load sample data for demonstration."""
    try:
        warehouse_data = pd.read_csv('data/warehouse_inventory.csv')
        orders_data = pd.read_csv('data/orders.csv')
        return warehouse_data, orders_data
    except FileNotFoundError as e:
        st.error(f"Sample data files not found: {e}")
        return None, None
    except Exception as e:
        st.error(f"Error loading sample data: {e}")
        return None, None

def main():
    st.markdown('<h1 class="main-header">Warehouse Inventory Optimizer</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Data Input")
    
    # File upload options
    data_source = st.sidebar.radio(
        "Choose data source:",
        ["Sample Data", "Upload Files"]
    )
    
    warehouse_data = None
    orders_data = None
    
    if data_source == "Sample Data":
        with st.spinner("Loading sample data..."):
            warehouse_data, orders_data = load_sample_data()
            if warehouse_data is not None and orders_data is not None:
                st.sidebar.success("Sample data loaded successfully!")
            else:
                st.sidebar.error("Sample data files not found. Please upload your own files.")
                data_source = "Upload Files"
    
    if data_source == "Upload Files":
        warehouse_file = st.sidebar.file_uploader(
            "Upload Warehouse Inventory CSV",
            type=['csv'],
            help="Required columns: Warehouse_ID, Location, Product_Category, Current_Stock_Units, Reorder_Level, Storage_Cost_per_Unit"
        )
        
        orders_file = st.sidebar.file_uploader(
            "Upload Orders CSV",
            type=['csv'],
            help="Required columns: Order_ID, Order_Date, Origin, Product_Category, Order_Value_INR"
        )
        
        if warehouse_file and orders_file:
            warehouse_data = pd.read_csv(warehouse_file)
            orders_data = pd.read_csv(orders_file)
            st.sidebar.success("Files uploaded successfully!")
    
    # Simulation parameters
    st.sidebar.header("Simulation Parameters")
    demand_change = st.sidebar.slider(
        "Demand Change (%)",
        min_value=-50.0,
        max_value=50.0,
        value=0.0,
        step=5.0,
        help="Simulate demand fluctuations"
    )
    
    cost_change = st.sidebar.slider(
        "Storage Cost Change (%)",
        min_value=-30.0,
        max_value=30.0,
        value=0.0,
        step=5.0,
        help="Simulate storage cost changes"
    )
    
    # Main content
    if warehouse_data is not None and orders_data is not None:
        # Validate data
        is_valid, errors = validate_data(warehouse_data, orders_data)
        
        if not is_valid:
            st.error("Data validation failed:")
            for error in errors:
                st.error(f"• {error}")
            return
        
        # Apply simulations
        if demand_change != 0:
            orders_data = simulate_demand_change(orders_data, demand_change / 100)
        
        if cost_change != 0:
            warehouse_data = simulate_cost_change(warehouse_data, cost_change / 100)
        
        # Process data with loading indicators
        with st.spinner("Processing data..."):
            demand_data = calculate_demand(orders_data)
            merged_data = compute_spi(warehouse_data, demand_data)
            recommendations = recommend_transfers(merged_data)
            metrics = calculate_metrics(merged_data)
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Overview", 
            "Stock Dashboard", 
            "Demand Forecast", 
            "Rebalancing", 
            "What-If Simulator"
        ])
        
        with tab1:
            st.header("Overview Dashboard")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total Warehouses",
                    value=metrics['total_warehouses']
                )
            
            with col2:
                st.metric(
                    label="Total SKUs",
                    value=metrics['total_skus']
                )
            
            with col3:
                st.metric(
                    label="Shortage %",
                    value=f"{metrics['shortage_percentage']}%",
                    delta=f"{metrics['shortage_percentage'] - 25}%" if metrics['shortage_percentage'] != 25 else None
                )
            
            with col4:
                st.metric(
                    label="Avg SPI",
                    value=metrics['average_spi'],
                    delta=f"{metrics['average_spi'] - 0:.2f}" if metrics['average_spi'] != 0 else None
                )
            
            # Cost savings and risk categories
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="success-card">', unsafe_allow_html=True)
                st.subheader("Potential Cost Savings")
                st.metric(
                    label="Total Estimated Savings",
                    value=f"₹{metrics['potential_cost_saving']:,}"
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="warning-card">', unsafe_allow_html=True)
                st.subheader("Top Risk Categories")
                for category, spi in metrics['top_risk_categories'].items():
                    st.write(f"• {category}: SPI = {spi:.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.header("Stock Dashboard")
            
            # SPI by warehouse
            spi_by_warehouse = merged_data.groupby('Location')['SPI'].mean().reset_index()
            spi_by_warehouse = spi_by_warehouse.sort_values('SPI')
            
            fig_spi = px.bar(
                spi_by_warehouse,
                x='Location',
                y='SPI',
                title='Stock Pressure Index by Warehouse',
                color='SPI',
                color_continuous_scale=['red', 'yellow', 'green']
            )
            fig_spi.update_layout(height=500)
            st.plotly_chart(fig_spi, use_container_width=True)
            
            # Stock vs Reorder Level heatmap
            pivot_data = merged_data.pivot_table(
                index='Location',
                columns='Product_Category',
                values='Current_Stock_Units',
                aggfunc='sum'
            )
            
            fig_heatmap = px.imshow(
                pivot_data,
                title='Current Stock Units by Warehouse and Category',
                color_continuous_scale='Blues'
            )
            fig_heatmap.update_layout(height=500)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Detailed stock table
            st.subheader("Detailed Stock Analysis")
            display_data = merged_data[['Warehouse_ID', 'Location', 'Product_Category', 
                                      'Current_Stock_Units', 'Reorder_Level', 'SPI']].copy()
            display_data['Status'] = display_data['SPI'].apply(
                lambda x: 'Surplus' if x > 0 else 'Shortage' if x < 0 else 'Balanced'
            )
            st.dataframe(display_data, width='stretch')
        
        with tab3:
            st.header("Demand Forecast")
            
            # Demand trends
            demand_trends = orders_data.copy()
            demand_trends['Order_Date'] = pd.to_datetime(demand_trends['Order_Date'])
            demand_trends['Month'] = demand_trends['Order_Date'].dt.to_period('M')
            
            monthly_demand = demand_trends.groupby(['Month', 'Product_Category']).size().reset_index(name='Demand')
            monthly_demand['Month'] = monthly_demand['Month'].astype(str)
            
            fig_demand = px.line(
                monthly_demand,
                x='Month',
                y='Demand',
                color='Product_Category',
                title='Demand Trends by Product Category'
            )
            fig_demand.update_layout(height=500)
            st.plotly_chart(fig_demand, use_container_width=True)
            
            # Predicted demand for next period
            st.subheader("Predicted Demand (Next Period)")
            predicted_demand = demand_data.copy()
            predicted_demand = predicted_demand.sort_values('Monthly_Demand', ascending=False)
            
            fig_predicted = px.bar(
                predicted_demand,
                x='Product_Category',
                y='Monthly_Demand',
                color='Origin',
                title='Predicted Demand by Category and Origin'
            )
            fig_predicted.update_layout(height=500)
            st.plotly_chart(fig_predicted, use_container_width=True)
        
        with tab4:
            st.header("Rebalancing Recommendations")
            
            if not recommendations.empty:
                st.subheader("Transfer Recommendations")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Transfers", len(recommendations))
                with col2:
                    st.metric("Total Units", recommendations['Units'].sum())
                with col3:
                    st.metric("Total Savings", f"₹{recommendations['Estimated_Saving_INR'].sum():,.2f}")
                
                # Recommendations table
                st.dataframe(recommendations, width='stretch')
                
                # Export functionality
                csv = recommendations.to_csv(index=False)
                st.download_button(
                    label="Download Recommendations CSV",
                    data=csv,
                    file_name="warehouse_transfer_recommendations.csv",
                    mime="text/csv"
                )
                
                # Visualization of transfers
                st.subheader("Transfer Network")
                
                # Create transfer network visualization
                fig_transfers = go.Figure()
                
                for _, row in recommendations.iterrows():
                    fig_transfers.add_trace(go.Scatter(
                        x=[row['From_Location'], row['To_Location']],
                        y=[1, 1],
                        mode='lines+markers',
                        line=dict(width=row['Units']/10, color='blue'),
                        marker=dict(size=10),
                        text=f"{row['Product_Category']}: {row['Units']} units",
                        hovertemplate=f"<b>{row['Product_Category']}</b><br>" +
                                    f"From: {row['From_Location']}<br>" +
                                    f"To: {row['To_Location']}<br>" +
                                    f"Units: {row['Units']}<br>" +
                                    f"Savings: ₹{row['Estimated_Saving_INR']}<extra></extra>",
                        showlegend=False
                    ))
                
                fig_transfers.update_layout(
                    title="Transfer Network Visualization",
                    xaxis_title="Warehouse Locations",
                    yaxis_title="",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_transfers, use_container_width=True)
                
            else:
                st.info("No transfer recommendations available. All warehouses are balanced!")
        
        with tab5:
            st.header("What-If Simulator")
            
            st.subheader("Current Simulation Parameters")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Demand Change", f"{demand_change:+.1f}%")
            with col2:
                st.metric("Cost Change", f"{cost_change:+.1f}%")
            
            # Show impact of current simulation
            st.subheader("Simulation Impact")
            
            # Compare original vs simulated metrics
            original_demand = calculate_demand(orders_data)
            original_merged = compute_spi(warehouse_data, original_demand)
            original_metrics = calculate_metrics(original_merged)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Shortage % Change",
                    f"{metrics['shortage_percentage'] - original_metrics['shortage_percentage']:+.2f}%",
                    delta=f"{metrics['shortage_percentage'] - original_metrics['shortage_percentage']:+.2f}%"
                )
            
            with col2:
                st.metric(
                    "Avg SPI Change",
                    f"{metrics['average_spi'] - original_metrics['average_spi']:+.2f}",
                    delta=f"{metrics['average_spi'] - original_metrics['average_spi']:+.2f}"
                )
            
            with col3:
                st.metric(
                    "Savings Change",
                    f"₹{metrics['potential_cost_saving'] - original_metrics['potential_cost_saving']:+,.2f}",
                    delta=f"₹{metrics['potential_cost_saving'] - original_metrics['potential_cost_saving']:+,.2f}"
                )
            
            # Interactive simulation controls
            st.subheader("Interactive Controls")
            st.write("Use the sidebar sliders to adjust simulation parameters and see real-time impact on the dashboard.")
            
            # Scenario analysis
            st.subheader("Scenario Analysis")
            
            scenarios = [
                {"name": "Best Case", "demand": -20, "cost": -10},
                {"name": "Worst Case", "demand": 30, "cost": 15},
                {"name": "Current", "demand": demand_change, "cost": cost_change}
            ]
            
            scenario_data = []
            for scenario in scenarios:
                sim_orders = simulate_demand_change(orders_data, scenario["demand"] / 100)
                sim_warehouse = simulate_cost_change(warehouse_data, scenario["cost"] / 100)
                sim_demand = calculate_demand(sim_orders)
                sim_merged = compute_spi(sim_warehouse, sim_demand)
                sim_metrics = calculate_metrics(sim_merged)
                
                scenario_data.append({
                    "Scenario": scenario["name"],
                    "Shortage %": sim_metrics['shortage_percentage'],
                    "Avg SPI": sim_metrics['average_spi'],
                    "Cost Savings": sim_metrics['potential_cost_saving']
                })
            
            scenario_df = pd.DataFrame(scenario_data)
            st.dataframe(scenario_df, width='stretch')
    
    else:
        st.info("Please upload your warehouse inventory and orders data using the sidebar, or use the sample data.")
        
        # Show sample data structure
        st.subheader("Expected Data Structure")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Warehouse Inventory CSV:**")
            st.code("""
Warehouse_ID,Location,Product_Category,Current_Stock_Units,Reorder_Level,Storage_Cost_per_Unit
W001,Mumbai,Electronics,150,50,25.5
W001,Mumbai,Clothing,200,75,15.0
W002,Delhi,Electronics,80,50,30.0
W002,Delhi,Clothing,120,75,18.5
            """)
        
        with col2:
            st.write("**Orders CSV:**")
            st.code("""
Order_ID,Order_Date,Origin,Product_Category,Order_Value_INR
ORD001,2024-01-15,Mumbai,Electronics,15000
ORD002,2024-01-16,Delhi,Clothing,8500
ORD003,2024-01-17,Mumbai,Electronics,22000
ORD004,2024-01-18,Delhi,Electronics,18000
            """)

if __name__ == "__main__":
    main()
