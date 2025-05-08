import sqlite3
import time
import statistics
import logging
import pandas as pd
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DBOperationBenchmarker:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.performance_data = []

    def benchmark_operation(self, operation: str, query: str, setup_queries: list = None, data: list = None, iterations: int = 3) -> dict:
        execution_times = []

        for _ in range(iterations):
            if setup_queries:
                try:
                    for setup_query in setup_queries:
                        if data and '?' in setup_query:
                            self.cursor.executemany(setup_query, data)
                        else:
                            self.cursor.execute(setup_query)
                    self.conn.commit()
                except sqlite3.Error as e:
                    logging.error(f"Setup for {operation} failed: {e}")
                    return {"error": str(e), "operation": operation, "query": query}

            start_time = time.time()
            try:
                if data and operation.upper() == "INSERT" and '?' in query:
                    self.cursor.executemany(query, data)
                else:
                    self.cursor.execute(query)
                self.conn.commit()
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
            except sqlite3.Error as e:
                logging.error(f"Operation {operation} failed: {e}")
                return {"error": str(e), "operation": operation, "query": query}

        return {
            "operation": operation.upper(),
            "query": query,
            "avg_time": statistics.mean(execution_times),
            "min_time": min(execution_times),
            "max_time": max(execution_times),
            "iterations": iterations
        }

    def analyze_operation(self, operation: str, query: str) -> list:
        suggestions = []
        query = query.lower().strip()
        operation = operation.upper()

        if operation == "CREATE":
            suggestions.append("Use appropriate data types for columns to optimize storage.")
            if "index" not in query:
                suggestions.append("Consider creating indexes after table creation for frequently queried columns.")
        if operation == "INSERT":
            suggestions.append("Use bulk inserts (executemany) for better performance.")
            suggestions.append("Disable indexes during large inserts and rebuild them after.")
        if operation == "SELECT":
            if "where" in query:
                suggestions.append("Create indexes on columns used in WHERE clauses.")
            if "join" in query:
                suggestions.append("Ensure joined columns have appropriate indexes.")
            if "*" in query:
                suggestions.append("Specify only needed columns instead of using *.")
        if operation == "UPDATE" or operation == "DELETE":
            if "where" in query:
                suggestions.append("Create indexes on columns used in WHERE clauses.")
            suggestions.append("Consider batching large UPDATE/DELETE operations.")
        if operation == "ALTER":
            suggestions.append("Avoid frequent ALTER operations on large tables; use maintenance windows.")

        return suggestions

    def run_benchmark_suite(self, operations: list) -> list:
        results = []
        for op, query, setup_queries, data in operations:
            result = self.benchmark_operation(op, query, setup_queries, data)
            # Always append the result, whether it has an error or not
            if "error" not in result:
                result["optimizations"] = self.analyze_operation(op, query)
                self.performance_data.append(result)
            results.append(result)
        return results

    def generate_performance_report(self, output_file: str = "db_operation_times.png"):
        if not self.performance_data:
            logging.warning("No performance data available for report")
            return

        df = pd.DataFrame(self.performance_data)
        all_ops = ['CREATE', 'INSERT', 'SELECT', 'UPDATE', 'DELETE', 'ALTER']
        
        # Ensure all operations are present in the DataFrame
        grouped = df.groupby('operation')['avg_time'].mean()
        grouped = grouped.reindex(all_ops, fill_value=0.0)

        plt.figure(figsize=(10, 6))
        bars = plt.bar(grouped.index, grouped.values, color='skyblue')
        plt.title('Average Execution Time by Operation')
        plt.ylabel('Average Time (seconds)')
        plt.xlabel('Database Operation')
        plt.grid(True, axis='y', linestyle='--', alpha=0.6)

        for bar, val in zip(bars, grouped.values):
            if val > 0:  # Only show labels for operations with valid data
                plt.text(bar.get_x() + bar.get_width()/2., val, f'{val:.4f}s', 
                        ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        logging.info(f"Performance report saved to {output_file}")

    def close(self):
        self.conn.close()
        logging.info("Database connection closed")

def main():
    benchmarker = DBOperationBenchmarker("operation_benchmark.db")

    insert_data = [
        (i, f'Test Emp {i}', f'Dept {i % 3}', 50000 + (i % 50) * 1000)
        for i in range(1, 101)
    ]

    test_operations = [
        ("CREATE", '''
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary REAL
            )
        ''', ["DROP TABLE IF EXISTS employees"], None),

        ("INSERT", '''
            INSERT INTO employees (id, name, department, salary)
            VALUES (?, ?, ?, ?)
        ''', [
            "DROP TABLE IF EXISTS employees",
            '''
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary REAL
            )
            '''
        ], insert_data),

        ("SELECT", '''
            SELECT * FROM employees WHERE department = 'Dept 1'
        ''', [
            "DROP TABLE IF EXISTS employees",
            '''
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary REAL
            )
            ''',
            '''
            INSERT INTO employees (id, name, department, salary)
            VALUES (?, ?, ?, ?)
            '''
        ], insert_data),

        ("UPDATE", '''
            UPDATE employees SET salary = salary + 1000
            WHERE department = 'Dept 1'
        ''', [
            "DROP TABLE IF EXISTS employees",
            '''
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary REAL
            )
            ''',
            '''
            INSERT INTO employees (id, name, department, salary)
            VALUES (?, ?, ?, ?)
            '''
        ], insert_data),

        ("DELETE", '''
            DELETE FROM employees
            WHERE salary < 51000
        ''', [
            "DROP TABLE IF EXISTS employees",
            '''
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary REAL
            )
            ''',
            '''
            INSERT INTO employees (id, name, department, salary)
            VALUES (?, ?, ?, ?)
            '''
        ], insert_data)
    ]

    results = benchmarker.run_benchmark_suite(test_operations)

    for result in results:
        print(f"\nOperation: {result['operation']}")
        print(f"Query: {result['query'].strip()}")
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Average Time: {result['avg_time']:.4f} seconds")
            print(f"Min Time: {result['min_time']:.4f} seconds")
            print(f"Max Time: {result['max_time']:.4f} seconds")
            print("Optimization Suggestions:")
            for suggestion in result.get('optimizations', []):
                print(f"- {suggestion}")

    benchmarker.generate_performance_report()
    benchmarker.close()

if __name__ == "__main__":
    main()