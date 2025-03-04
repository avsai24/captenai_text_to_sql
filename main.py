import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
import json
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")
database_url = os.getenv("DATABASE_FOLDER")

genai.configure(api_key=api_key)  

arr = []

PROMPT = """
You are an expert AI assistant specializing in converting **natural language questions** into **optimized SQL queries** based on available databases.

You **must strictly follow these guidelines**:

---

### ** Databases and Their Tables**
#### **Sports Databases**
- **players.db** → PLAYERS (**player_id, name, team_id, position, goals, assists, matches**)  
- **teams.db** → TEAMS (**team_id, team_name, stadium_id, wins, losses, draws, points, finance_id**)  
- **stadiums.db** → STADIUMS (**stadium_id, name, city, capacity, weather_impact**)  
- **financials.db** → FINANCIALS (**finance_id, team_id, player_salary, transfer_fee, club_revenue**)  

####  **Real Estate Databases**
- **homes.db** → HOMES (**home_id, owner_name, address, city, state, zip_code, num_bedrooms, num_bathrooms, square_footage, property_value**)  
- **land.db** → LAND_PLOTS (**plot_id, home_id, area_sqft, land_use_type, zoning_code, property_value**)  
- **utilities.db** → UTILITIES (**utility_id, home_id, electricity_provider, electricity_bill, gas_provider, gas_bill, last_bill_date**)  
- **water.db** → WATER_SUPPLY (**supply_id, home_id, water_source, daily_usage_gallons, last_bill_date, amount_due**)  

####  **General Purpose Databases**
- **student.db** → STUDENT (**name, class, age, marks**)  
- **employees.db** → EMPLOYEES (**name, department, salary, experience**)  
- **sales.db** → SALES (**product, region, sales, revenue**)  

---

### ** Query Processing Rules**
1. **Check Required Databases**  
   - Identify which tables contain relevant information.
   - If only one database is needed, generate a single query.
   - If multiple databases are needed, generate **multiple queries** ensuring **a valid relational merge** is possible.

2. **Strictly Enforce Data Relationships**  
   - Only generate multi-database queries **if a valid common key exists**.  
   - **Examples of valid relationships:**
     - **players.db ↔ teams.db** (via `team_id`)
     - **teams.db ↔ stadiums.db** (via `stadium_id`)
     - **teams.db ↔ financials.db** (via `finance_id`)
     - **homes.db ↔ land.db** (via `home_id`)
     - **homes.db ↔ utilities.db** (via `home_id`)
     - **homes.db ↔ water.db** (via `home_id`)

   - **If no common key exists, strictly return:**  
     ```plaintext
     Your question is not related between databases.
     ```

3. **Return Queries in Structured JSON Format**
   - If a valid query exists:
   ```json
   {
       "queries": [
           {
               "database": "<DB_NAME>",
               "sql": "<SQL_QUERY>"
           }
       ]
   }
   ```
   - If **multiple databases** are needed:
   ```json
   {
       "queries": [
           {
               "database": "players.db",
               "sql": "SELECT player_id, name, team_id FROM PLAYERS"
           },
           {
               "database": "teams.db",
               "sql": "SELECT team_id, team_name, stadium_id FROM TEAMS"
           },
           {
               "database": "stadiums.db",
               "sql": "SELECT stadium_id, name AS stadium_name, city FROM STADIUMS"
           }
       ]
   }
   ```
   - **If multiple databases have no relationship, strictly return:**
     ```plaintext
     Your question is not related between databases.
     ```

---

### ** Example Scenarios**
#### ** User Input:**  
*"Show me all players and their teams along with the stadiums they play in."*
#### ** Expected Output:**  
```json
{
    "queries": [
        {
            "database": "players.db",
            "sql": "SELECT player_id, name, team_id FROM PLAYERS"
        },
        {
            "database": "teams.db",
            "sql": "SELECT team_id, team_name, stadium_id FROM TEAMS"
        },
        {
            "database": "stadiums.db",
            "sql": "SELECT stadium_id, name AS stadium_name, city FROM STADIUMS"
        }
    ]
}
```

#### ** User Input:**  
*"How many goals did Ronaldo score and what is the total sales revenue?"*
#### ** Strict Expected Output:**  
```plaintext
Your question is not related between databases.
```

#### ** User Input:**  
*"Get all player goals and property values of homes."*
#### ** Strict Expected Output:**  
```plaintext
Your question is not related between databases.
```

---

### ** Error Handling**
- **Invalid Request:**  
  *"Show me the number of flights in 2024."*  
  ```plaintext
  I don’t have enough info.
  ```
- **Multiple Databases Without Relation:**  
  *"Get all player goals and property values of homes."*  
  ```plaintext
  Your question is not related between databases.
  ```

---

### **Final Notes**
    Always generate only **valid SQL queries**.  
    Maintain **database relationships** when merging.  
    If no relationship exists, **strictly return 'Your question is not related between databases.'**  
    Never assume missing data.  

---
Now convert any natural language question into structured SQL queries!


"""

def dynamic_query_executor(sql_query, primary_db):
    db_path = os.path.join(database_url, primary_db)

    if not os.path.exists(db_path):
        st.error(f"Error: Database '{primary_db}' not found in '{database_url}'.")
        return None
    try:
        conn = sqlite3.connect(db_path)
        
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        if df.empty:    
            return None
        return df

    except sqlite3.Error as e:
        return None
    except Exception as e:
        return None

def get_sql_query_and_db(question):

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([PROMPT, question])
    response  = response.text.strip()
    return response

def clean_json_string(json_string):
    if not json_string or json_string.strip() == "":
        st.error("Error: The string is empty or None.")
        return {"error": "Empty response received."}
    
    if json_string.startswith("```json") and json_string.endswith("```"):
        json_string = json_string[7:-3].strip()

    try:
        return json.loads(json_string) 
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return {"error": "Invalid JSON format."}

def get_final_response(question, df):
    prompt_2 = f"""
Analyze the dataset based on the provided user question and generate a strictly validated structured response.

## ** Input:**
- **User Question**: {question}
- **Final DataFrame**: {df} (Do NOT hallucinate missing data)

---

## ** Strict Validation Before Answering**
### ** A. Direct Answer Rules**
- If the dataset **fully answers the question**, return a **concise direct answer**.
- If **data is missing or unrelated**, explicitly state **"Insufficient data to answer."**  
- If **multiple databases are queried** but **have no valid relationship**, return:
  ```plaintext
  Your question is not related between databases.
  ```

---

### ** B. Visualization Validation Rules**
1. **Determine if visualization is required** (`"Yes"` or `"No"`).
2. **Check Numeric Data Requirement for Charts**:
   - If **both selected columns are categorical**, return:
     ```json
     {{ "visualization_required": "No", "chart_type": null }}
     ```
   - If at least **one column is numeric**, suggest a valid chart type.
   - If **no numeric data is available**, explicitly state:
     ```json
     {{ "visualization_required": "No", "chart_type": null, "direct_answer": "No numerical data available for visualization." }}
     ```

---

### ** C. Chart Selection Rules**
- **Histograms**: Require **exactly one numeric column**. If categorical columns are selected, return **Bar Chart** instead.
- **Bar Charts**: Require **one categorical (X-axis) and one numeric column (Y-axis)**.
- **Scatter Plots**: Require **two numeric columns**.
- **Line Charts**: Require **one categorical/time-based X-axis** and **one numeric Y-axis**.
- **Pie Charts**: Require **one categorical (X-axis) and one numeric column (Y-axis)**. If there are **>10 unique categories**, return:
  ```json
  {{ "visualization_required": "No", "direct_answer": "Too many categories for pie chart." }}
  ```

---

## ** Structured JSON Response Format**
```json
{{
  "direct_answer": "<Concise answer based on available data>",
  "visualization_required": "<Yes/No>",
  "chart_type": "<Suggested chart type or null>",
  "columns_for_visualization": ["<Column1>", "<Column2>"] or null
}}
```

---

## ** Example Scenarios**

### ** Case 1: Direct Answer, No Visualization**
**User Question:** *"What is the average salary of employees?"*  
**Final DataFrame:**
```
Employee  Salary
A        60000
B        75000
C        80000
```
**AI Response:**
```json
{{
  "direct_answer": "The average salary of employees is $71,667.",
  "visualization_required": "No",
  "chart_type": null,
  "columns_for_visualization": null
}}
```

---

### ** Case 2: Visualization Recommended**
**User Question:** *"How does salary vary across departments?"*  
**Final DataFrame:**
```
Department  Salary
HR         50000
IT         90000
Sales      70000
```
**AI Response:**
```json
{{
  "direct_answer": "The dataset contains salary information categorized by department.",
  "visualization_required": "Yes",
  "chart_type": "Bar Chart",
  "columns_for_visualization": ["Department", "Salary"]
}}
```

---

### ** Case 3: Insufficient Data**
**User Question:** *"What is the average salary of employees?"*  
**Final DataFrame:**
```
Employee  Age
A        25
B        30
C        28
```
**AI Response:**
```json
{{
  "direct_answer": "The dataset does not contain salary-related information to answer this question.",
  "visualization_required": "No",
  "chart_type": null,
  "columns_for_visualization": null
}}
```

---

### ** Case 4: Preventing Invalid Visualization**
**User Question:** *"Retrieve homes along with their utility providers."*  
**Final DataFrame:**
```
home_id  owner_name  address         electricity_provider  gas_provider
1        John Doe    112 Oak St      Green Energy          Eco Gas
2        Jane Smith  557 Maple Ave   National Grid        City Gas
```
**AI Response:**
```json
{{
  "direct_answer": "The data presents homes along with their electricity and gas providers.",
  "visualization_required": "No",
  "chart_type": null,
  "columns_for_visualization": null
}}
```

---

### ** Case 5: Handling Unrelated Database Queries**
**User Question:** *"How many goals did Ronaldo score and what is the total revenue from sales?"*  
**Final DataFrame:** **(Data exists but from unrelated databases)**  
**AI Response:**  
```plaintext
Your question is not related between databases.
```

---

### ** Strict Rules Applied:**
    **Prevents histograms with categorical data (Suggests Bar Chart instead).**  
    **Ensures Pie Charts have ≤10 unique categories.**  
    **Validates numeric data before recommending visualization.**  
    **Strictly prevents unrelated multi-database queries.**  

---

## ** Final Takeaways**
- **Now, AI will only generate valid chart recommendations.**   
- **If visualization is not possible, it will explicitly state why.**   
- **Strict handling of unrelated multi-database queries.**   
- **Prevents incorrect histograms (e.g., categorical data)** by auto-suggesting bar charts. 

Your **AI-powered chart recommendation system** is now **bulletproof!** 


"""

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt_2)
    response  = response.text.strip()
    return response

def merge_arr(arr):
    if len(arr) == 1:
        return arr[0]  
    
    merged_df = arr[0] 

    for df in arr[1:]:
        common_cols = list(set(merged_df.columns) & set(df.columns)) 

        if common_cols:
            merged_df = pd.merge(merged_df, df, on=common_cols[0], how='inner')  
        else:
            st.error("No common columns found between DataFrames. Cannot merge.")
            return None
    return merged_df

def chart_type_determine(chart_type):
    if "bar" in chart_type.lower():
        return "bar"
    elif "line" in chart_type.lower():
        return "line"
    elif "scatter" in chart_type.lower():
        return "scatter"
    elif "histogram" in chart_type.lower():
        return "histogram"
    elif "pie" in chart_type.lower():
        return "pie"
    else:
        return None

def generate_chart(df, chart_type, columns):
    
    if not columns or not isinstance(columns, list) or len(columns) == 0:
        st.error("Error: No valid columns provided for visualization!")
        return

    df.columns = df.columns.str.strip()
    columns = [col.strip() for col in columns]

    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        st.error(f"Error: The following columns are missing in DataFrame: {missing_cols}")
        return
    x_col = columns[0]
    y_col = columns[1] if len(columns) > 1 else None  

    if x_col not in df.columns:
        st.error(f"Error: Column '{x_col}' not found in DataFrame.")
        return

    # df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    # if y_col:
    #     df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

   
    if chart_type.lower() == "histogram":
        if not pd.api.types.is_numeric_dtype(df[x_col]):
            st.error(f"Error: Column '{x_col}' is not numeric. Cannot plot histogram.")
            return

        fig, ax = plt.subplots(figsize=(8, 5))
        df[x_col].plot(kind="hist", ax=ax, bins=10, color='blue', edgecolor='black')

        ax.set_title(f"Distribution of {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel("Frequency")

        st.pyplot(fig)
        return 

    
    fig, ax = plt.subplots(figsize=(8, 5))

    if chart_type.lower() == "bar":
        if y_col is None:
            st.error("Error: Bar chart requires both X and Y columns.")
            return
        df.plot(kind="bar", x=x_col, y=y_col, ax=ax, color='skyblue')
        ax.set_title(f"{y_col} by {x_col}")

    elif chart_type.lower() == "line":
        if y_col is None:
            st.error("Error: Line chart requires both X and Y columns.")
            return
        df.plot(kind="line", x=x_col, y=y_col, ax=ax, marker='o', linestyle='-')
        ax.set_title(f"Trend of {y_col} over {x_col}")

    elif chart_type.lower() == "scatter":
        if y_col is None:
            st.error("Error: Scatter plot requires both X and Y columns.")
            return
        df.plot(kind="scatter", x=x_col, y=y_col, ax=ax, color='blue')
        ax.set_title(f"{x_col} vs {y_col}")

    elif chart_type.lower() == "pie":
        if y_col is None:
            st.error("Error: Pie chart requires a category and a numeric column.")
            return
        if df[x_col].nunique() > 10:
            st.error("Error: Pie chart requires ≤10 unique categories.")
            return
        df.set_index(x_col)[y_col].plot(kind="pie", autopct="%1.1f%%", ax=ax, startangle=90, cmap="Set3")
        plt.ylabel("")
        ax.set_title(f"Distribution of {y_col}")

    else:
        st.error("Error: Unsupported chart type!")
        return

    st.pyplot(fig)


st.title("CaptenAI: Smart SQL Query & Visualization Engine")

question = st.text_input("Enter your question")
submit = st.button("Generate")

if submit:
    response = get_sql_query_and_db(question)

    if "queries" not in response:
        st.write(f"**CaptenAi Response**: Your question is not related between databases.")
    else:
        response_dict = clean_json_string(response)

        for result in response_dict["queries"]:
            database = result["database"]
            sql_query = result["sql"]
            df = dynamic_query_executor(sql_query, database)

            if df is None:
                st.write(f"**CaptenAi Response**: Unable to retrieve data from Database. Please try different Question.")

            arr.append(df)
        if len(arr)!=0:
            final_df= merge_arr(arr)
            
            if final_df is not None:
                final_response = get_final_response(question, final_df)
                final_response_dict = clean_json_string(final_response)
                
                if final_response_dict.get("visualization_required") == "Yes":
                        chart_type = final_response_dict.get("chart_type")
                        columns = final_response_dict.get("columns_for_visualization")
                        chart_type = chart_type_determine(chart_type)

                        result = final_response_dict.get("direct_answer")
                        st.markdown(f"**CaptenAi Response**: {result}")
                        st.markdown(f"**Results Retrieved**:")
                        st.table(final_df)
                        if chart_type and columns:
                            generate_chart(final_df, chart_type, columns)
                        
                else:
                    result = final_response_dict.get("direct_answer")
                    st.markdown(f"**CaptenAi Response**: {result}")
                    st.markdown(f"**Results Retrieved**:")
                    st.table(final_df)