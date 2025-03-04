# CaptenAI: Smart SQL Query & Visualization Engine

## Overview
CaptenAI is an intelligent system designed to convert natural language queries into SQL queries and visualize the extracted data. It supports multiple structured databases, ensuring valid relational queries and preventing unrelated cross-database queries. The system is designed to strictly adhere to database relationships and return structured results in JSON format.

## Features
- Converts natural language queries into optimized SQL queries.
- Ensures database relationships before merging results.
- Returns structured JSON responses with strict validation.
- Provides automatic chart recommendations for visual representation.
- Supports multiple databases and prevents unrelated queries.

## Technology Stack
- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** SQLite
- **Machine Learning:** Google Generative AI (Gemini-2.0 Flash)
- **Visualization:** Matplotlib

## Database Schema
### Sports Databases
- **players.db** → PLAYERS (*player_id, name, team_id, position, goals, assists, matches*)
- **teams.db** → TEAMS (*team_id, team_name, stadium_id, wins, losses, draws, points, finance_id*)
- **stadiums.db** → STADIUMS (*stadium_id, name, city, capacity, weather_impact*)
- **financials.db** → FINANCIALS (*finance_id, team_id, player_salary, transfer_fee, club_revenue*)

### Real Estate Databases
- **homes.db** → HOMES (*home_id, owner_name, address, city, state, zip_code, num_bedrooms, num_bathrooms, square_footage, property_value*)
- **land.db** → LAND_PLOTS (*plot_id, home_id, area_sqft, land_use_type, zoning_code, property_value*)
- **utilities.db** → UTILITIES (*utility_id, home_id, electricity_provider, electricity_bill, gas_provider, gas_bill, last_bill_date*)
- **water.db** → WATER_SUPPLY (*supply_id, home_id, water_source, daily_usage_gallons, last_bill_date, amount_due*)

### General Purpose Databases
- **student.db** → STUDENT (*name, class, age, marks*)
- **employees.db** → EMPLOYEES (*name, department, salary, experience*)
- **sales.db** → SALES (*product, region, sales, revenue*)

## Query Processing
### Steps
1. **Extract User Query**: Identify the intent and required databases.
2. **Generate SQL Queries**: Convert the question into structured SQL.
3. **Execute Queries**: Retrieve relevant data from the respective databases.
4. **Validate Data Relationships**: Ensure data is relational before merging.
5. **Process and Return Results**: Format the output in JSON or visual format.

### Example Query and Response
#### User Input
"Show me all players and their teams along with the stadiums they play in."

#### Output JSON
```json
{
    "queries": [
        { "database": "players.db", "sql": "SELECT player_id, name, team_id FROM PLAYERS" },
        { "database": "teams.db", "sql": "SELECT team_id, team_name, stadium_id FROM TEAMS" },
        { "database": "stadiums.db", "sql": "SELECT stadium_id, name AS stadium_name, city FROM STADIUMS" }
    ]
}
```

## Visualization
CaptenAI determines the best visualization type based on query output. Supported visualizations include:
- **Bar Chart**: Categorical vs Numeric data
- **Line Chart**: Trends over time
- **Scatter Plot**: Relationship between two numeric values
- **Histogram**: Distribution of numeric values
- **Pie Chart**: Proportional representation (limited to 10 categories)

### Example Response for Visualization
```json
{
  "direct_answer": "The dataset contains salary information categorized by department.",
  "visualization_required": "Yes",
  "chart_type": "Bar Chart",
  "columns_for_visualization": ["Department", "Salary"]
}
```

## Error Handling
- If databases are unrelated: "Your question is not related between databases."
- If data is missing: "Insufficient data to answer."
- If invalid query: "I don’t have enough info."

## Setup Instructions
### Prerequisites
- Python 3.8+
- SQLite3
- Virtual Environment Setup (Optional but recommended)

### Installation Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/captenai_text_to_sql.git
   ```
2. Navigate to the project folder:
   ```sh
   cd captenai_text_to_sql
   ```
3. Set up a virtual environment:
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
5. Set up environment variables in `.env`:
   ```sh
   API_KEY=your_gemini_api_key
   DATABASE_FOLDER=your_database_path
   ```
6. Run the application:
   ```sh
   streamlit run app.py
   ```

## Contribution Guidelines
1. Fork the repository and create a new branch.
2. Make your changes and test thoroughly.
3. Submit a pull request with a detailed description.

## License
This project is licensed under the MIT License.

