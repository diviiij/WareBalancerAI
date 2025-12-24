# Warehouse Inventory Optimizer

An AI-powered warehouse inventory optimization system that uses demand forecasting and linear optimization to recommend optimal stock transfers between warehouses, reducing costs and improving service levels.

## Features

- **Demand Forecasting**: Predict future demand using historical order patterns
- **Stock Pressure Index (SPI)**: Calculate inventory pressure for each warehouse-product combination
- **Smart Recommendations**: Generate optimal transfer recommendations between warehouses
- **What-If Analysis**: Simulate different scenarios with interactive sliders
- **Interactive Dashboards**: Visualize data with Plotly charts and graphs
- **Cost Optimization**: Minimize total logistics costs while maintaining service levels

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. **Clone or download the project**
   ```bash
   cd intelligent_warehouse_balancer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:8501` to access the application.

## Data Structure

### Warehouse Inventory CSV (`data/warehouse_inventory.csv`)
Required columns:
- `Warehouse_ID`: Unique identifier for each warehouse
- `Location`: Geographic location (city/region)
- `Product_Category`: Product category (Electronics, Clothing, etc.)
- `Current_Stock_Units`: Current inventory level
- `Reorder_Level`: Minimum stock threshold
- `Storage_Cost_per_Unit`: Cost per unit for storage (INR)

### Orders CSV (`data/orders.csv`)
Required columns:
- `Order_ID`: Unique order identifier
- `Order_Date`: Date of the order (YYYY-MM-DD format)
- `Origin`: Origin location (should match warehouse locations)
- `Product_Category`: Product category
- `Order_Value_INR`: Order value in Indian Rupees

## How to Use

### 1. Data Input
- **Option A**: Use the provided sample data for testing
- **Option B**: Upload your own CSV files using the sidebar

### 2. Dashboard Navigation
The application has 5 main tabs:

#### Overview
- Key metrics and KPIs
- Total warehouses, SKUs, shortage percentage
- Potential cost savings
- Top risk categories

#### Stock Dashboard
- Stock Pressure Index (SPI) visualization
- Stock vs Reorder Level heatmap
- Detailed stock analysis table

#### Demand Forecast
- Historical demand trends
- Predicted demand for next period
- Category-wise demand patterns

#### Rebalancing
- Transfer recommendations table
- Transfer network visualization
- CSV export functionality

#### What-If Simulator
- Interactive simulation controls
- Scenario analysis (Best Case, Worst Case, Current)
- Real-time impact visualization

### 3. Simulation Parameters
Use the sidebar sliders to:
- **Demand Change**: Simulate demand fluctuations (-50% to +50%)
- **Storage Cost Change**: Simulate cost variations (-30% to +30%)

## Key Algorithms

### Stock Pressure Index (SPI)
```
SPI = (Current_Stock_Units - Reorder_Level) - Predicted_Demand
```
- **Negative SPI**: Shortage risk (needs stock)
- **Positive SPI**: Surplus (can donate stock)
- **Zero SPI**: Balanced inventory

### Transfer Optimization
1. Identify warehouses with SPI < 0 (shortage)
2. Find warehouses with SPI > 0 (surplus) for same product category
3. Calculate optimal transfer units
4. Estimate cost savings

### Cost Savings Calculation
```
Savings = Transfer_Units × (Donor_Storage_Cost - Receiver_Storage_Cost)
```

## Sample Outputs

### Key Metrics
- **Total Warehouses**: 8
- **Total SKUs**: 32
- **Shortage %**: 25.0%
- **Average SPI**: -5.2
- **Potential Cost Saving**: ₹15,250

### Transfer Recommendations
| Product_Category | From_Location | To_Location | Units | Estimated_Saving_INR |
|------------------|---------------|-------------|-------|---------------------|
| Electronics      | Bangalore     | Delhi       | 30    | 240.00              |
| Clothing         | Mumbai        | Pune        | 25    | 125.00              |
| Books            | Chennai       | Kolkata     | 15    | 30.00               |

## Screenshots

### Main Dashboard
![Dashboard](https://via.placeholder.com/800x400/1f77b4/ffffff?text=Main+Dashboard)

### Stock Pressure Index
![SPI Chart](https://via.placeholder.com/800x400/ff7f0e/ffffff?text=SPI+Visualization)

### Transfer Network
![Transfer Network](https://via.placeholder.com/800x400/2ca02c/ffffff?text=Transfer+Network)

## Troubleshooting

### Common Issues

1. **File Upload Errors**
   - Ensure CSV files have correct column names
   - Check date format (YYYY-MM-DD)
   - Verify numeric columns don't contain text

2. **No Recommendations Generated**
   - Check if warehouses have both surplus and shortage
   - Verify product categories match between files
   - Ensure sufficient data for demand calculation

3. **Performance Issues**
   - Large datasets may take time to process
   - Consider filtering data for testing
   - Use sample data for initial testing

### Data Validation
The application automatically validates:
- Required columns presence
- Negative stock or cost values
- Date format consistency
- Data type compatibility

## Advanced Features

### Linear Optimization (Future Enhancement)
The system is designed to support PuLP-based linear optimization:
- Minimize total transfer costs
- Subject to stock constraints
- Consider distance and transportation costs

### Custom Distance Matrix
For production use, implement:
- Real distance calculations between locations
- Transportation cost factors
- Delivery time constraints

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify your data format matches requirements
3. Test with sample data first
4. Check console for error messages

## Updates

### Version 1.0
- Initial release with core functionality
- Sample data and basic optimization
- Interactive dashboards and what-if analysis

### Planned Features
- Advanced optimization algorithms
- Real-time data integration
- Multi-objective optimization
- Machine learning demand forecasting

---

**Built with Streamlit, Pandas, and Plotly**
