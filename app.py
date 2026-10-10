
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="European Banking – Customer Churn Analytics",
    page_icon="📊",
    layout="wide"
)

DATA_FILE = Path(__file__).parent / "Customer-Churn-Records.xlsx"

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE, sheet_name="Customer-Churn-Records")

    # Make labels easier to use in charts
    df["Churn Label"] = df["Exited"].map({0: "Retained", 1: "Churned"})
    df["Active Label"] = df["IsActiveMember"].map({0: "Inactive", 1: "Active"})
    df["Card Label"] = df["HasCrCard"].map({0: "No Credit Card", 1: "Has Credit Card"})
    return df

df = load_data()

# -------------------------
# Sidebar filters
# -------------------------
st.sidebar.title("🔎 Dashboard Filters")

geographies = sorted(df["Geography"].dropna().unique().tolist())
genders = sorted(df["Gender"].dropna().unique().tolist())
age_groups = sorted(df["Age Group"].dropna().unique().tolist())
credit_tiers = sorted(df["Credit Tier"].dropna().unique().tolist())
balance_statuses = sorted(df["Balance Status"].dropna().unique().tolist())
card_types = sorted(df["Card Type"].dropna().unique().tolist())

selected_geo = st.sidebar.multiselect("Geography", geographies, default=geographies)
selected_gender = st.sidebar.multiselect("Gender", genders, default=genders)
selected_age = st.sidebar.multiselect("Age Group", age_groups, default=age_groups)
selected_credit = st.sidebar.multiselect("Credit Tier", credit_tiers, default=credit_tiers)
selected_balance = st.sidebar.multiselect("Balance Status", balance_statuses, default=balance_statuses)
selected_card = st.sidebar.multiselect("Card Type", card_types, default=card_types)

min_age, max_age = int(df["Age"].min()), int(df["Age"].max())
age_range = st.sidebar.slider("Age Range", min_age, max_age, (min_age, max_age))

min_balance, max_balance = float(df["Balance"].min()), float(df["Balance"].max())
balance_range = st.sidebar.slider(
    "Balance Range",
    min_value=float(min_balance),
    max_value=float(max_balance),
    value=(float(min_balance), float(max_balance)),
    step=1000.0
)

active_options = st.sidebar.multiselect(
    "Membership Status",
    ["Active", "Inactive"],
    default=["Active", "Inactive"]
)

filtered = df[
    df["Geography"].isin(selected_geo)
    & df["Gender"].isin(selected_gender)
    & df["Age Group"].isin(selected_age)
    & df["Credit Tier"].isin(selected_credit)
    & df["Balance Status"].isin(selected_balance)
    & df["Card Type"].isin(selected_card)
    & df["Age"].between(age_range[0], age_range[1])
    & df["Balance"].between(balance_range[0], balance_range[1])
    & df["Active Label"].isin(active_options)
].copy()

# -------------------------
# Helper functions
# -------------------------
def pct(x):
    return f"{x:.2f}%"

def churn_rate(data):
    return data["Exited"].mean() * 100 if len(data) else 0

# -------------------------
# Header
# -------------------------
st.title("🇪🇺 European Banking – Customer Churn Analytics")
st.caption(
    "Interactive customer segmentation, churn analysis and financial-risk dashboard "
    "built from the provided banking customer dataset."
)

if filtered.empty:
    st.warning("No customers match the selected filters. Please broaden your filters.")
    st.stop()

# -------------------------
# KPI cards
# -------------------------
total_customers = len(filtered)
churned = int(filtered["Exited"].sum())
retained = total_customers - churned
overall_churn = churn_rate(filtered)
avg_balance = filtered["Balance"].mean()
churned_balance = filtered.loc[filtered["Exited"] == 1, "Balance"].sum()
high_value_threshold = df["Balance"].quantile(0.75)
high_value = filtered[filtered["Balance"] >= high_value_threshold]
high_value_churn_rate = churn_rate(high_value) if len(high_value) else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Customers", f"{total_customers:,}")
c2.metric("Churned", f"{churned:,}")
c3.metric("Churn Rate", pct(overall_churn))
c4.metric("Retained", f"{retained:,}")
c5.metric("Avg. Balance", f"€{avg_balance:,.0f}")
c6.metric("High-Value Churn", pct(high_value_churn_rate))

st.divider()

# -------------------------
# Tabs
# -------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "👥 Segmentation", "💰 High-Value Risk", "📈 Comparisons", "📋 Data"]
)

with tab1:
    st.subheader("Overall Churn Summary")

    col1, col2 = st.columns(2)

    with col1:
        status = filtered["Churn Label"].value_counts().reset_index()
        status.columns = ["Status", "Customers"]
        fig = px.pie(
            status,
            names="Status",
            values="Customers",
            hole=0.45,
            title="Churned vs Retained Customers"
        )
        fig.update_layout(legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        geo = (
            filtered.groupby("Geography")
            .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
            .reset_index()
        )
        geo["Churn_Rate"] *= 100
        fig = px.bar(
            geo,
            x="Geography",
            y="Churn_Rate",
            text="Churn_Rate",
            title="Geography-wise Churn Rate",
            labels={"Churn_Rate": "Churn Rate (%)"}
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Churn by Gender and Geography")
    gender_geo = (
        filtered.groupby(["Geography", "Gender"])
        .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
        .reset_index()
    )
    gender_geo["Churn_Rate"] *= 100

    fig = px.bar(
        gender_geo,
        x="Geography",
        y="Churn_Rate",
        color="Gender",
        barmode="group",
        text="Churn_Rate",
        title="Gender-based Churn Differences by Geography",
        labels={"Churn_Rate": "Churn Rate (%)"}
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Customer Segmentation")

    col1, col2 = st.columns(2)

    with col1:
        age = (
            filtered.groupby("Age Group")
            .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
            .reset_index()
        )
        age["Churn_Rate"] *= 100
        fig = px.bar(
            age,
            x="Age Group",
            y="Churn_Rate",
            text="Churn_Rate",
            title="Age-group Churn Rate",
            labels={"Churn_Rate": "Churn Rate (%)"}
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        credit = (
            filtered.groupby("Credit Tier")
            .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
            .reset_index()
        )
        credit["Churn_Rate"] *= 100
        fig = px.bar(
            credit,
            x="Credit Tier",
            y="Churn_Rate",
            text="Churn_Rate",
            title="Credit Tier vs Churn",
            labels={"Churn_Rate": "Churn Rate (%)"}
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        tenure = (
            filtered.groupby("Tenure")
            .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
            .reset_index()
        )
        tenure["Churn_Rate"] *= 100
        fig = px.line(
            tenure,
            x="Tenure",
            y="Churn_Rate",
            markers=True,
            title="Tenure vs Churn Rate",
            labels={"Churn_Rate": "Churn Rate (%)"}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        products = (
            filtered.groupby("NumOfProducts")
            .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
            .reset_index()
        )
        products["Churn_Rate"] *= 100
        fig = px.bar(
            products,
            x="NumOfProducts",
            y="Churn_Rate",
            text="Churn_Rate",
            title="Number of Products vs Churn",
            labels={"Churn_Rate": "Churn Rate (%)"}
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Balance Segment Analysis")
    bal = (
        filtered.groupby("Balance Status")
        .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
        .reset_index()
    )
    bal["Churn_Rate"] *= 100
    fig = px.bar(
        bal,
        x="Balance Status",
        y="Churn_Rate",
        text="Churn_Rate",
        title="Balance Status vs Churn",
        labels={"Churn_Rate": "Churn Rate (%)"}
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("High-Value Customer Churn Analysis")

    st.info(
        f"High-value customers are defined here as customers with balance at or above "
        f"the dataset's 75th percentile: €{high_value_threshold:,.0f}."
    )

    hv1, hv2, hv3, hv4 = st.columns(4)
    hv_churned = int(high_value["Exited"].sum())
    hv1.metric("High-Value Customers", f"{len(high_value):,}")
    hv2.metric("High-Value Churners", f"{hv_churned:,}")
    hv3.metric("High-Value Churn Rate", pct(high_value_churn_rate))
    hv4.metric("Churned Balance at Risk", f"€{high_value.loc[high_value['Exited']==1,'Balance'].sum():,.0f}")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.scatter(
            filtered,
            x="Balance",
            y="EstimatedSalary",
            color="Churn Label",
            size="CreditScore",
            hover_data=["Geography", "Age", "NumOfProducts", "IsActiveMember"],
            title="Balance vs Estimated Salary",
            labels={"EstimatedSalary": "Estimated Salary (€)", "Balance": "Balance (€)"}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        hv_geo = (
            high_value.groupby("Geography")
            .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
            .reset_index()
        )
        hv_geo["Churn_Rate"] *= 100
        fig = px.bar(
            hv_geo,
            x="Geography",
            y="Churn_Rate",
            text="Churn_Rate",
            title="High-Value Churn by Geography",
            labels={"Churn_Rate": "Churn Rate (%)"}
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("High-Value Churner Profile")
    hv_churners = high_value[high_value["Exited"] == 1]

    if len(hv_churners):
        profile = pd.DataFrame({
            "Metric": [
                "Average Age",
                "Average Credit Score",
                "Average Balance",
                "Average Salary",
                "Average Products",
                "Active Member %",
                "Complaint %",
            ],
            "Value": [
                f"{hv_churners['Age'].mean():.1f}",
                f"{hv_churners['CreditScore'].mean():.0f}",
                f"€{hv_churners['Balance'].mean():,.0f}",
                f"€{hv_churners['EstimatedSalary'].mean():,.0f}",
                f"{hv_churners['NumOfProducts'].mean():.2f}",
                f"{hv_churners['IsActiveMember'].mean()*100:.1f}%",
                f"{hv_churners['Complain'].mean()*100:.1f}%",
            ]
        })
        st.dataframe(profile, use_container_width=True, hide_index=True)
    else:
        st.warning("No high-value churners match the current filters.")

with tab4:
    st.subheader("Comparative Demographic Analysis")

    col1, col2 = st.columns(2)

    with col1:
        activity = (
            filtered.groupby("Active Label")
            .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
            .reset_index()
        )
        activity["Churn_Rate"] *= 100
        fig = px.bar(
            activity,
            x="Active Label",
            y="Churn_Rate",
            text="Churn_Rate",
            title="Active vs Inactive Member Churn",
            labels={"Churn_Rate": "Churn Rate (%)"}
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        complaint = (
            filtered.groupby("Complain")
            .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
            .reset_index()
        )
        complaint["Complaint Status"] = complaint["Complain"].map({0: "No Complaint", 1: "Complaint"})
        complaint["Churn_Rate"] *= 100
        fig = px.bar(
            complaint,
            x="Complaint Status",
            y="Churn_Rate",
            text="Churn_Rate",
            title="Complaint Status vs Churn",
            labels={"Churn_Rate": "Churn Rate (%)"}
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Financial Stability vs Churn")
    financial = (
        filtered.assign(
            Balance_Band=pd.qcut(
                filtered["Balance"].rank(method="first"),
                4,
                labels=["Low Balance", "Lower-Mid", "Upper-Mid", "High Balance"]
            )
        )
        .groupby("Balance_Band", observed=False)
        .agg(Customers=("CustomerId", "count"), Churn_Rate=("Exited", "mean"))
        .reset_index()
    )
    financial["Churn_Rate"] *= 100

    fig = px.bar(
        financial,
        x="Balance_Band",
        y="Churn_Rate",
        text="Churn_Rate",
        title="Balance Quartile vs Churn",
        labels={"Churn_Rate": "Churn Rate (%)"}
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Filtered Customer Records")

    display_cols = [
        "CustomerId", "Surname", "Geography", "Gender", "Age",
        "CreditScore", "Tenure", "Balance", "NumOfProducts",
        "IsActiveMember", "EstimatedSalary", "Exited",
        "Satisfaction Score", "Card Type", "Age Group",
        "Credit Tier", "Balance Status"
    ]

    st.dataframe(
        filtered[display_cols].sort_values("Balance", ascending=False),
        use_container_width=True,
        height=500
    )

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_customer_churn_data.csv",
        mime="text/csv"
    )

# -------------------------
# Footer
# -------------------------
st.divider()
st.caption(
    "Project: Customer Segmentation & Churn Pattern Analytics in European Banking | "
    f"Records shown: {len(filtered):,} of {len(df):,}"
)
