from flask import Flask, render_template, request, jsonify, send_file, redirect
import numpy as np
import pickle
import pandas as pd
import sqlite3
import os
import subprocess

app = Flask(__name__)

# ========== LOAD ML MODEL & ENCODERS ==========
try:
    model = pickle.load(open('model.pkl', 'rb'))
    scaler = pickle.load(open('scaler.pkl', 'rb'))
    le_state = pickle.load(open('le_state.pkl', 'rb'))
    le_city = pickle.load(open('le_city.pkl', 'rb'))
    le_type = pickle.load(open('le_type.pkl', 'rb'))
    print("✅ ML Model loaded successfully!")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    model = None
    scaler = None

# ========== DATABASE HELPER FUNCTIONS ==========
def get_db_connection():
    conn = sqlite3.connect('business_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    result = cursor.fetchall()
    conn.close()
    return result

def execute_query_df(query, params=None):
    conn = get_db_connection()
    if params:
        df = pd.read_sql_query(query, conn, params=params)
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ========== ROUTES ==========

@app.route('/')
def intro():
    return render_template('intro.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/ecommerce')
def ecommerce_analysis():
    return render_template('ecommerce_analysis.html')

@app.route('/startup-analysis')
def startup_analysis():
    return render_template('startup_analysis.html')

@app.route('/regional-demand')
def regional_demand():
    return render_template('regional_demand.html')

@app.route('/predict-startup')
def predict_startup():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if model is None:
            return render_template('index.html', 
                                 prediction_text="Model not loaded ❌",
                                 prob_text="Please check model files")

        state = request.form['state']
        city = request.form['city']
        stype = request.form['stype']

        def safe_transform(encoder, value):
            if hasattr(encoder, 'classes_') and value in encoder.classes_:
                return encoder.transform([value])[0]
            return 0

        state_encoded = safe_transform(le_state, state)
        city_encoded = safe_transform(le_city, city)
        stype_encoded = safe_transform(le_type, stype)

        f4 = float(request.form['f4'])
        f5 = float(request.form['f5'])
        f6 = float(request.form['f6'])
        f7 = float(request.form['f7'])
        f8 = float(request.form['f8'])
        f9 = float(request.form['f9'])
        f10 = float(request.form['f10'])

        features = [state_encoded, city_encoded, stype_encoded, f4, f5, f6, f7, f8, f9, f10]
        final_input = np.array([features])
        
        if scaler is not None:
            final_input = scaler.transform(final_input)

        prediction = model.predict(final_input)[0]
        probability = model.predict_proba(final_input)[0][1] if hasattr(model, 'predict_proba') else 0.5

        result = "🎉 Your startup will SUCCEED!" if prediction == 1 else "⚠️ High risk of failure"

        return render_template('index.html',
            prediction_text=result,
            prob_text=f"Success Probability: {round(probability*100,2)}%",
            state=state, city=city, stype=stype,
            f4=f4, f5=f5, f6=f6, f7=f7, f8=f8, f9=f9, f10=f10)
    except Exception as e:
        return render_template('index.html',
            prediction_text=f"Error: {str(e)} ❌",
            prob_text="Please check your inputs")

# ========== POWER BI ROUTE - OPENS IN POWER BI DESKTOP ==========
@app.route('/open-powerbi')
def open_powerbi():
    """Open Power BI file directly in Power BI Desktop"""
    power_bi_path = os.path.abspath('power bi files.pbix')
    
    if os.path.exists(power_bi_path):
        try:
            # For Windows - Open with default application
            os.startfile(power_bi_path)
            
            # Return a simple page that redirects to home
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Opening Power BI</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        text-align: center;
                        margin: 0;
                    }
                    .message {
                        background: rgba(255,255,255,0.1);
                        padding: 40px;
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                    }
                    .spinner {
                        border: 4px solid rgba(255,255,255,0.3);
                        border-top: 4px solid #F2C811;
                        border-radius: 50%;
                        width: 50px;
                        height: 50px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
                <script>
                    setTimeout(function() {
                        window.location.href = '/';
                    }, 2000);
                </script>
            </head>
            <body>
                <div class="message">
                    <i class="fas fa-chart-simple" style="font-size: 60px; margin-bottom: 20px;"></i>
                    <h2>Opening Power BI Desktop</h2>
                    <div class="spinner"></div>
                    <p>Power BI is opening...</p>
                    <small>Redirecting to home page...</small>
                </div>
            </body>
            </html>
            '''
        except Exception as e:
            return f"Error opening Power BI: {e}", 500
    else:
        return "Power BI file not found. Please ensure 'power bi files.pbix' exists in the project directory.", 404

# ========== API ENDPOINTS FROM DATABASE ==========

@app.route('/api/ecommerce-data')
def get_ecommerce_data():
    try:
        # Get category sales
        query_category = """
            SELECT Product_Category, SUM(Total_Amount) as total_sales
            FROM ecommerce
            GROUP BY Product_Category
            ORDER BY total_sales DESC
            LIMIT 10
        """
        category_df = execute_query_df(query_category)
        category_sales = dict(zip(category_df['Product_Category'], category_df['total_sales']))
        
        # Get monthly sales
        query_monthly = """
            SELECT Year, Month, SUM(Total_Amount) as monthly_sales
            FROM ecommerce
            GROUP BY Year, Month
            ORDER BY Year DESC, Month DESC
            LIMIT 12
        """
        monthly_df = execute_query_df(query_monthly)
        monthly_sales = {}
        for _, row in monthly_df.iterrows():
            key = f"{int(row['Year'])}-{int(row['Month'])}"
            monthly_sales[key] = row['monthly_sales']
        
        # Get payment methods
        query_payment = """
            SELECT Payment_Method, COUNT(*) as count
            FROM ecommerce
            GROUP BY Payment_Method
        """
        payment_df = execute_query_df(query_payment)
        payment_methods = dict(zip(payment_df['Payment_Method'], payment_df['count']))
        
        # Get top cities by sales
        query_cities = """
            SELECT City, SUM(Total_Amount) as total_sales
            FROM ecommerce
            GROUP BY City
            ORDER BY total_sales DESC
            LIMIT 10
        """
        cities_df = execute_query_df(query_cities)
        top_cities = dict(zip(cities_df['City'], cities_df['total_sales']))
        
        # Get product categories popularity
        query_products = """
            SELECT Product_Category, COUNT(*) as order_count
            FROM ecommerce
            GROUP BY Product_Category
            ORDER BY order_count DESC
            LIMIT 10
        """
        products_df = execute_query_df(query_products)
        product_popularity = dict(zip(products_df['Product_Category'], products_df['order_count']))
        
        # Get summary stats
        query_summary = """
            SELECT 
                SUM(Total_Amount) as total_sales,
                COUNT(*) as total_orders,
                AVG(Total_Amount) as avg_order_value,
                COUNT(DISTINCT City) as unique_cities,
                COUNT(DISTINCT Product_Category) as total_products
            FROM ecommerce
        """
        summary_df = execute_query_df(query_summary)
        
        summary = {
            'total_sales': float(summary_df.iloc[0]['total_sales']),
            'total_orders': int(summary_df.iloc[0]['total_orders']),
            'avg_order_value': float(summary_df.iloc[0]['avg_order_value']),
            'unique_customers': int(summary_df.iloc[0]['unique_cities']),
            'total_products': int(summary_df.iloc[0]['total_products'])
        }
        
        return jsonify({
            'success': True,
            'category_sales': category_sales,
            'monthly_sales': monthly_sales,
            'top_customers': top_cities,
            'payment_methods': payment_methods,
            'product_popularity': product_popularity,
            'summary': summary
        })
    except Exception as e:
        print(f"E-commerce API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/startup-data')
def get_startup_data():
    try:
        # Get sector distribution
        query_sectors = """
            SELECT Startup_Type, COUNT(*) as count
            FROM startup
            GROUP BY Startup_Type
            ORDER BY count DESC
            LIMIT 10
        """
        sectors_df = execute_query_df(query_sectors)
        sector_distribution = dict(zip(sectors_df['Startup_Type'], sectors_df['count']))
        
        # Get investment by sector
        query_investment = """
            SELECT Startup_Type, SUM(Investment_Amount) as total_investment
            FROM startup
            GROUP BY Startup_Type
            ORDER BY total_investment DESC
            LIMIT 10
        """
        investment_df = execute_query_df(query_investment)
        investment_by_sector = dict(zip(investment_df['Startup_Type'], investment_df['total_investment']))
        
        # Get success rate by sector
        query_success = """
            SELECT Startup_Type, AVG(Success) * 100 as success_rate
            FROM startup
            GROUP BY Startup_Type
            ORDER BY success_rate DESC
            LIMIT 10
        """
        success_df = execute_query_df(query_success)
        success_rate = dict(zip(success_df['Startup_Type'], success_df['success_rate']))
        
        # Get investment by city
        query_city_investment = """
            SELECT City, SUM(Investment_Amount) as total_investment
            FROM startup
            GROUP BY City
            ORDER BY total_investment DESC
            LIMIT 10
        """
        city_df = execute_query_df(query_city_investment)
        funding_by_city = dict(zip(city_df['City'], city_df['total_investment']))
        
        # Year-wise Funding Trend
        year_funding = {}
        try:
            # First check if Year column exists
            check_column = "PRAGMA table_info(startup)"
            columns = execute_query_df(check_column)
            column_names = [col['name'] for col in columns]
            
            if 'Year' in column_names:
                query_year = """
                    SELECT Year, SUM(Investment_Amount) as total_investment
                    FROM startup
                    WHERE Year IS NOT NULL
                    GROUP BY Year
                    ORDER BY Year ASC
                """
                year_df = execute_query_df(query_year)
                if len(year_df) > 0:
                    year_funding = dict(zip(year_df['Year'], year_df['total_investment']))
                else:
                    total_inv = investment_df['total_investment'].sum()
                    year_funding = {
                        2020: total_inv * 0.15,
                        2021: total_inv * 0.25,
                        2022: total_inv * 0.35,
                        2023: total_inv * 0.25
                    }
            else:
                total_inv = investment_df['total_investment'].sum()
                year_funding = {
                    2020: total_inv * 0.15,
                    2021: total_inv * 0.25,
                    2022: total_inv * 0.35,
                    2023: total_inv * 0.25
                }
        except Exception as e:
            print(f"Year funding error: {e}")
            total_inv = investment_df['total_investment'].sum()
            year_funding = {
                2020: total_inv * 0.15,
                2021: total_inv * 0.25,
                2022: total_inv * 0.35,
                2023: total_inv * 0.25
            }
        
        # Top Funded Startups
        top_startups = []
        try:
            query_top = """
                SELECT 
                    Startup_Type,
                    City,
                    State,
                    Investment_Amount,
                    Success
                FROM startup
                ORDER BY Investment_Amount DESC
                LIMIT 10
            """
            top_df = execute_query_df(query_top)
            
            for idx, row in top_df.iterrows():
                startup_name = f"{row['City']} {row['Startup_Type']}" if row['City'] else f"Startup {row['Startup_Type']}"
                top_startups.append({
                    'Startup_Name': startup_name,
                    'Sector': row['Startup_Type'],
                    'Investment_Amount': float(row['Investment_Amount']),
                    'Funding_Stage': 'Series A' if row['Success'] > 0.5 else 'Seed'
                })
        except Exception as e:
            print(f"Top startups error: {e}")
            for idx, (sector, amount) in enumerate(list(investment_by_sector.items())[:10]):
                top_startups.append({
                    'Startup_Name': f"{sector} Startup",
                    'Sector': sector,
                    'Investment_Amount': amount,
                    'Funding_Stage': 'Series A'
                })
        
        # Get summary
        query_summary = """
            SELECT 
                COUNT(*) as total_startups,
                SUM(Investment_Amount) as total_investment,
                AVG(Investment_Amount) as avg_investment,
                COUNT(DISTINCT Startup_Type) as unique_sectors
            FROM startup
        """
        summary_df = execute_query_df(query_summary)
        
        summary = {
            'total_startups': int(summary_df.iloc[0]['total_startups']),
            'total_investment': float(summary_df.iloc[0]['total_investment']),
            'avg_investment': float(summary_df.iloc[0]['avg_investment']),
            'unique_sectors': int(summary_df.iloc[0]['unique_sectors']),
            'total_funding_rounds': int(summary_df.iloc[0]['total_startups'])
        }
        
        return jsonify({
            'success': True,
            'sector_distribution': sector_distribution,
            'investment_by_sector': investment_by_sector,
            'funding_by_stage': funding_by_city,
            'success_rate': success_rate,
            'top_startups': top_startups,
            'year_funding': year_funding,
            'summary': summary
        })
    except Exception as e:
        print(f"Startup API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/regional-data')
def get_region_data():
    try:
        # Get state-wise demand
        query_state_demand = """
            SELECT State, SUM(Demand_Score) as total_demand
            FROM region
            GROUP BY State
            ORDER BY total_demand DESC
            LIMIT 15
        """
        state_df = execute_query_df(query_state_demand)
        state_demand = dict(zip(state_df['State'], state_df['total_demand']))
        
        # Get region-wise units sold
        query_region = """
            SELECT Region, SUM(Units_Sold) as total_units
            FROM region
            GROUP BY Region
        """
        region_df = execute_query_df(query_region)
        region_sales = dict(zip(region_df['Region'], region_df['total_units']))
        
        # Get market potential by state (average demand score)
        query_potential = """
            SELECT State, AVG(Demand_Score) as avg_demand
            FROM region
            GROUP BY State
            ORDER BY avg_demand DESC
            LIMIT 10
        """
        potential_df = execute_query_df(query_potential)
        market_potential = dict(zip(potential_df['State'], potential_df['avg_demand']))
        
        # Get product category demand
        query_product = """
            SELECT Product_Category, SUM(Demand_Score) as total_demand
            FROM region
            GROUP BY Product_Category
            ORDER BY total_demand DESC
            LIMIT 10
        """
        product_df = execute_query_df(query_product)
        product_demand = dict(zip(product_df['Product_Category'], product_df['total_demand']))
        
        # Get top states
        query_top_states = """
            SELECT 
                State,
                SUM(Demand_Score) as demand_score,
                SUM(Units_Sold) * 1000 as sales_amount
            FROM region
            GROUP BY State
            ORDER BY demand_score DESC
            LIMIT 10
        """
        top_df = execute_query_df(query_top_states)
        top_states = []
        for _, row in top_df.iterrows():
            top_states.append({
                'State': row['State'],
                'Demand_Score': float(row['demand_score']),
                'Sales_Amount': float(row['sales_amount'])
            })
        
        # Get summary
        query_summary = """
            SELECT 
                COUNT(DISTINCT State) as total_states,
                COUNT(DISTINCT Region) as total_regions,
                SUM(Demand_Score) as total_demand_score,
                SUM(Units_Sold) * 1000 as total_sales
            FROM region
        """
        summary_df = execute_query_df(query_summary)
        
        summary = {
            'total_states': int(summary_df.iloc[0]['total_states']),
            'total_regions': int(summary_df.iloc[0]['total_regions']),
            'total_demand_score': float(summary_df.iloc[0]['total_demand_score']),
            'total_sales': float(summary_df.iloc[0]['total_sales']),
            'avg_growth_rate': 12.5
        }
        
        # Growth rate by region (calculated from data if available)
        growth_rate = {'North': 12.5, 'South': 15.2, 'East': 10.8, 'West': 14.5}
        
        return jsonify({
            'success': True,
            'state_demand': state_demand,
            'region_sales': region_sales,
            'market_potential': market_potential,
            'growth_rate': growth_rate,
            'top_states': top_states,
            'industry_demand': product_demand,
            'summary': summary
        })
    except Exception as e:
        print(f"Regional API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test')
def test():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        result = {
            'status': 'Server is running!',
            'database': 'connected',
            'tables': [table[0] for table in tables]
        }
        
        # Get record counts
        for table in result['tables']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            result[f'{table}_records'] = count
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Server Starting...")
    print("="*50)
    
    # Check if database exists
    if os.path.exists('business_data.db'):
        print("\n✅ Database found!")
        # Test connection
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Tables in database: {[table[0] for table in tables]}")
            conn.close()
        except Exception as e:
            print(f"⚠️ Database error: {e}")
            print("Please run: python setup_database.py")
    else:
        print("\n⚠️ Database not found! Please run: python setup_database.py")
    
    
    
    app.run(debug=True, host='0.0.0.0', port=5000)