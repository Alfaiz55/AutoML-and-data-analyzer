import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, silhouette_score

# =========================
# 1. LOAD DATA
# =========================
def load_data(file_path):
    try:
        if file_path.endswith('.csv'):
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding="latin1")
                except:
                    df = pd.read_csv(file_path, encoding="ISO-8859-1")

        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)

        else:
            return None

        return df

    except:
        return None


# =========================
# 2. DETECT PROBLEM TYPE
# =========================
def detect_problem_type(df, target=None):

    if target is None:
        return "clustering"

    if target not in df.columns:
        return None

    if df[target].dtype == 'object' or df[target].nunique() <= 10:
        return "classification"
    else:
        return "regression"


# =========================
# 3. PREPROCESS
# =========================
def preprocess_data(df, target):

    df = df.copy()

    # Fill missing
    for col in df.select_dtypes(include=['int64','float64']):
        df[col].fillna(df[col].median(), inplace=True)

    for col in df.select_dtypes(include=['object']):
        df[col].fillna(df[col].mode()[0], inplace=True)

    # Encode
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()

    for col in df.select_dtypes(include=['object']):
        df[col] = le.fit_transform(df[col])

    if target is not None:
        X = df.drop(columns=[target])
        y = df[target]
    else:
        X = df
        y = None

    from sklearn.preprocessing import StandardScaler
    X = StandardScaler().fit_transform(X)

    return X, y


# =========================
# 4. TRAIN MODELS
# =========================
def train_models(X, y, problem_type):

    results = {}

    from sklearn.model_selection import train_test_split

    if problem_type != "clustering":
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    # ---------- CLASSIFICATION ----------
    if problem_type == "classification":

        from sklearn.tree import DecisionTreeClassifier
        from sklearn.svm import SVC

        models = {
            "Logistic Regression": LogisticRegression(max_iter=1000),
            "Decision Tree": DecisionTreeClassifier(),
            "Random Forest": RandomForestClassifier(),
            "SVM": SVC()
        }

        for name, model in models.items():
            model.fit(X_train, y_train)
            results[name] = accuracy_score(y_test, model.predict(X_test))

    # ---------- REGRESSION ----------
    elif problem_type == "regression":

        from sklearn.tree import DecisionTreeRegressor
        from sklearn.svm import SVR
        from sklearn.metrics import r2_score

        models = {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(),
            "Random Forest": RandomForestRegressor(),
            "SVR": SVR()
        }

        for name, model in models.items():
            model.fit(X_train, y_train)
            results[name] = r2_score(y_test, model.predict(X_test))

    # ---------- CLUSTERING ----------
    elif problem_type == "clustering":

        from sklearn.cluster import KMeans, AgglomerativeClustering
        from sklearn.mixture import GaussianMixture

        best_score = -1
        best_model = None

        for k in range(2, 6):

            for name, model in {
                "KMeans": KMeans(n_clusters=k, random_state=42),
                "Agglomerative": AgglomerativeClustering(n_clusters=k),
                "GaussianMixture": GaussianMixture(n_components=k, random_state=42)
            }.items():

                try:
                    labels = model.fit_predict(X)
                    score = silhouette_score(X, labels)

                    model_name = f"{name} (k={k})"
                    results[model_name] = score

                    if score > best_score:
                        best_score = score
                        best_model = model_name

                except:
                    pass

        results["BEST_MODEL"] = best_model
        results["BEST_SCORE"] = best_score

    return results


# =========================
# 5. SELECT BEST
# =========================
def select_best_model(results, problem_type):

    if problem_type == "clustering":
        return results.get("BEST_MODEL"), results.get("BEST_SCORE")
    else:
        best = max(results, key=results.get)
        return best, results[best]


# =========================
# 6. INSIGHTS
# =========================
def generate_insights(df, best_model, best_score, problem_type):

    if problem_type == "clustering":
        return f"""
Clustering completed using {best_model}
Best silhouette score: {round(best_score,4)}
Multiple algorithms and cluster sizes were tested.
"""
    else:
        return f"""
Best model selected: {best_model}
Score: {round(best_score,4)}
Model chosen based on performance comparison.
"""


# =========================
# 7. VISUALIZATION
# =========================
def smart_visualization(df, target):

    plots = []

    try:
        # ===== Target Distribution =====
        if target and target in df.columns:
            fig, ax = plt.subplots()
            df[target].value_counts().plot(kind='bar', ax=ax)
            ax.set_title("Target Distribution")
            plots.append(fig)

        # ===== Numerical Features =====
        num_cols = df.select_dtypes(include=['int64','float64']).columns

        for col in num_cols[:3]:
            fig, ax = plt.subplots()
            df[col].plot(kind='hist', bins=20, ax=ax)
            ax.set_title(f"{col} Distribution")
            plots.append(fig)

        # ===== Correlation Heatmap =====
        if len(num_cols) > 1:
            fig, ax = plt.subplots()
            sns.heatmap(df[num_cols].corr(), annot=True, ax=ax)
            ax.set_title("Correlation Heatmap")
            plots.append(fig)

    except Exception as e:
        print("Visualization error:", e)

    return plots


# =========================
# 8. PIPELINE
# =========================
def run_pipeline(file_path, target=None):

    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    try:
        df = load_data(file_path)
        if df is None:
            return {"error": "Data loading failed"}

        problem_type = detect_problem_type(df, target)

        X, y = preprocess_data(df, target)

        results = train_models(X, y, problem_type)

        best_model, best_score = select_best_model(results, problem_type)

        insights = generate_insights(df, best_model, best_score, problem_type)

        plots = smart_visualization(df, target if target else df.columns[0])

        return {
            "problem_type": problem_type,
            "best_model": best_model,
            "score": best_score,
            "all_results": results,   # 🔥 IMPORTANT
            "insights": insights,    # 🔥 IMPORTANT
            "logs": mystdout.getvalue(),
            "plots": plots
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        sys.stdout = old_stdout