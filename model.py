import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_echarts import st_echarts
import uuid
import re

from storage import (
    add_idea,
    get_all,
    update_idea,
    load_permissions,
    add_user,
    update_role,
    delete_user
)

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="EFS Turbo Drive", layout="wide")

st.markdown(
    "<h1 style='text-align:center;'>EFS TURBO DRIVE</h1>",
    unsafe_allow_html=True
)

df = pd.DataFrame()

# =========================================================
# CLEAN
# =========================================================

def clean(x):
    if pd.isna(x):
        return None
    x = str(x).replace("\u00a0", "")
    x = x.strip().lower()
    x = re.sub(r"\s+", " ", x)
    return x


def clean_df(df):
    df = df.copy()

    for col in ["idea", "idea_name", "status", "rejection_reason", "name", "project", "category"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    if "roi" in df.columns:
        df["roi"] = pd.to_numeric(df["roi"], errors="coerce").fillna(0)

    return df


# =========================================================
# PERMISSIONS
# =========================================================

permission_data = load_permissions()
user_df = pd.DataFrame(permission_data)

if not user_df.empty:
    user_df.columns = [clean(c) for c in user_df.columns]
    user_df["email"] = user_df["email"].apply(clean)
    user_df["role"] = user_df["role"].apply(clean)
else:
    user_df = pd.DataFrame(columns=["email", "role"])

email_role_map = dict(zip(user_df["email"], user_df["role"]))

role_page_map = {
    "super user": ["Submit Idea", "PL Assignment", "Feasibility", "Approval", "Dashboard", "Admin"],
    "normal user": ["Submit Idea"],
    "automation engineer": ["Submit Idea", "Feasibility", "Dashboard"],
    "automation pl": ["Submit Idea", "PL Assignment", "Feasibility", "Approval", "Dashboard"],
    "pl/spl": ["Submit Idea", "Approval", "Dashboard"]
}

# =========================================================
# LOGIN
# =========================================================

st.sidebar.title("Login")

email_input = st.sidebar.text_input("Enter Email ID")
user_email = clean(email_input)
role = email_role_map.get(user_email)

if not user_email:
    st.warning("Enter email")
    st.stop()

if role is None:
    st.error("Access Denied")
    st.stop()

st.sidebar.success(f"Role: {role.title()}")

menu = st.sidebar.selectbox("Menu", role_page_map.get(role, []))

# =========================================================
# SUBMIT IDEA
# =========================================================

if menu == "Submit Idea":

    st.subheader("Submit Idea")

    pl_users = sorted(
        user_df[user_df["role"].isin(["pl/spl", "automation pl"])]["email"].dropna().tolist()
    )

    with st.form("submit"):

        name = st.text_input("Name")
        idea_name = st.text_input("Idea Name")
        idea = st.text_area("Idea")

        project = st.selectbox("Project", ["CA-MRO", "BA-MRO", "BA-LCE", "CA-LCE", "Controls"])
        category = st.selectbox("Type", ["Customer Requirement", "Internal"])
        pl_name = st.selectbox("PL", pl_users)

        submit = st.form_submit_button("Submit")

    if submit:

        add_idea({
            "id": str(uuid.uuid4()),
            "name": name,
            "idea_name": idea_name,
            "idea": idea,
            "project": project,
            "category": category,
            "pl_name": pl_name,
            "status": "New Idea",
            "roi": 0,
            "assigned_engineer": "",
            "feasibility_data": {},
            "feasibility_comments": "",
            "decision": "",
            "rejection_reason": "",
            "approval_comment": "",
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "assigned_date": "",
            "wip_date": "",
            "uat_date": "",
            "completion_date": ""
        })

        st.success("Submitted")

# =========================================================
# PL ASSIGNMENT
# =========================================================

elif menu == "PL Assignment":

    st.subheader("Assign Engineer")

    df = clean_df(pd.DataFrame(get_all()))

    for item in df.to_dict("records"):

        if item["status"] == "New Idea":

            st.markdown(f"💡 {item['idea']}")

            eng = st.text_input("Engineer", key=f"eng_{item['id']}")

            if st.button("Assign", key=f"a_{item['id']}"):

                update_idea(item["id"], {
                    "assigned_engineer": eng,
                    "status": "Assigned",
                    "assigned_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

                st.rerun()

# =========================================================
# FEASIBILITY
# =========================================================

elif menu == "Feasibility":

    st.subheader("Feasibility")

    df = clean_df(pd.DataFrame(get_all()))

    for item in df.to_dict("records"):

        if item["status"] == "Assigned":

            st.markdown(f"### {item['idea']}")

            manual = st.number_input("Manual", key=f"m_{item['id']}")
            fte = st.number_input("FTE", key=f"f_{item['id']}")
            eng = st.number_input("Auto Effort", key=f"e_{item['id']}")

            freq = st.selectbox("Freq", ["Daily","Weekly","Monthly","Yearly"], key=f"fr_{item['id']}")

            multiplier = {"Daily":260,"Weekly":52,"Monthly":12,"Yearly":1}

            roi = (manual * fte * multiplier[freq]) / (eng if eng else 1)

            st.info(f"ROI: {round(roi,2)}")

            if st.button("Submit", key=f"fs_{item['id']}"):

                update_idea(item["id"], {
                    "status": "WIP",
                    "roi": roi,
                    "wip_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

                st.rerun()

# =========================================================
# APPROVAL
# =========================================================

elif menu == "Approval":

    st.subheader("Approval")

    df = clean_df(pd.DataFrame(get_all()))

    pl_list = df["pl_name"].dropna().unique().tolist()

    pl_user = st.selectbox("Select PL", [""] + sorted(pl_list))

    if not pl_user:
        st.stop()

    data = df[(df["status"] == "WIP") & (df["pl_name"] == pl_user)]

    for item in data.to_dict("records"):

        st.markdown(f"### {item['idea']}")

        decision = st.radio("Decision", ["GO","NO-GO"], key=f"d_{item['id']}")

        comment = st.text_area("Comment", key=f"c_{item['id']}")

        if st.button("Submit", key=f"ap_{item['id']}"):

            new_status = "UAT" if decision == "GO" else "Rejected"

            update_idea(item["id"], {
                "status": new_status,
                "decision": decision,
                "approval_comment": comment
            })

            st.rerun()

# =========================================================
# DASHBOARD (WITH KANBAN FIXED)
# =========================================================

elif menu == "Dashboard":

    st.subheader("Dashboard")

    df = clean_df(pd.DataFrame(get_all()))

    if df.empty:
        st.stop()

    # KPI
    c1, c2 = st.columns(2)

    with c1:
        st.metric("Customer ROI", df[df["category"]=="Customer Requirement"]["roi"].sum())

    with c2:
        st.metric("Internal ROI", df[df["category"]=="Internal"]["roi"].sum())

    # =========================================================
    # TREE
    # =========================================================
    st.subheader(" Ideation Tree")

    def count(d, status):
        return len(d[d["status"] == status])

    def reject(d, reason):
        return len(d[
            (d["status"] == "Rejected") &
            (d["rejection_reason"] == reason)
        ])

    def build_tree(d):

        return [

            {
                "name": f"Queued ({count(d,'New Idea')})",
                "label": {
                    "backgroundColor": "#2563EB",
                    "color": "#FFFFFF",
                    "borderColor": "#60A5FA"
                }
            },

            {
                "name": f"Feasibility ({count(d,'Assigned')})",
                "label": {
                    "backgroundColor": "#2563EB",
                    "color": "#FFFFFF",
                    "borderColor": "#60A5FA"
                }
            },

            {
                "name": f"WIP ({count(d,'WIP')})",
                "label": {
                    "backgroundColor": "#16A34A",
                    "color": "#FFFFFF",
                    "borderColor": "#4ADE80"
                }
            },

            {
                "name": f"UAT ({count(d,'UAT')})",
                "label": {
                    "backgroundColor": "#16A34A",
                    "color": "#FFFFFF",
                    "borderColor": "#4ADE80"
                }
            },

            {
                "name": f"Completed ({count(d,'Completed')})",
                "label": {
                    "backgroundColor": "#16A34A",
                    "color": "#FFFFFF",
                    "borderColor": "#4ADE80"
                }
            },

            {
                "name": f"Rejected ({count(d,'Rejected')})",
                "label": {
                    "backgroundColor": "#16A34A",
                    "color": "#FFFFFF",
                    "borderColor": "#4ADE80"
                },

                "children": [

                    {
                        "name": f"Technical ({reject(d,'Technical Rejection')})",
                        "label": {
                            "backgroundColor": "#16A34A",
                            "color": "#FFFFFF",
                            "borderColor": "#4ADE80"
                        }
                    },

                    {
                        "name": f"Business ({reject(d,'Business Rejection')})",
                        "label": {
                            "backgroundColor": "#16A34A",
                            "color": "#FFFFFF",
                            "borderColor": "#4ADE80"
                        }
                    }
                ]
            }
        ]

    customer_df = df[df["category"] == "Customer Requirement"]
    internal_df = df[df["category"] == "Internal"]

    tree = {

        "name": f"EFS IDEATION ({len(df)})",

        "label": {
            "backgroundColor": "#EA580C",
            "color": "#FFFFFF",
            "borderColor": "#FDBA74"
        },

        "children": [

            {
                "name": f"Customer ({len(customer_df)})",

                "label": {
                    "backgroundColor": "#EA580C",
                    "color": "#FFFFFF",
                    "borderColor": "#FDBA74"
                },

                "children": build_tree(customer_df)
            },

            {
                "name": f"Internal ({len(internal_df)})",

                "label": {
                    "backgroundColor": "#EA580C",
                    "color": "#FFFFFF",
                    "borderColor": "#FDBA74"
                },

                "children": build_tree(internal_df)
            }
        ]
    }

    option = {

        "backgroundColor": "#0B0B0D",

        "series": [{

            "type": "tree",

            "data": [tree],

            "symbol": "roundRect",

            "orient": "LR",

            "expandAndCollapse": True,

            "initialTreeDepth": -1,

            "top": "5%",
            "bottom": "5%",
            "left": "18%",
            "right": "20%",

            "label": {

                "color": "#FFFFFF",

                "fontSize": 11,

                "fontWeight": "bold",

                "backgroundColor": "#1E1E24",

                "borderColor": "#FF6A00",

                "borderWidth": 2,

                "borderRadius": 6,

                "padding": [6, 12],

                "width": 170,

                "lineHeight": 18,

                "overflow": "break",

                "distance": 40,

                "formatter": "{b}"
            },

            "leaves": {

                "label": {

                    "width": 170,

                    "overflow": "break"
                }
            },

            "lineStyle": {

                "color": "#FF6A00",

                "width": 2
            },

            "emphasis": {

                "focus": "descendant",

                "label": {

                    "backgroundColor": "#FF6A00",

                    "color": "#000"
                }
            }
        }]
    }

    st_echarts(option, height="550px")

    st.divider()

    # =========================================================
    # KANBAN BOARD
    # =========================================================
    st.subheader("Kanban Planner Board")

    statuses = ["New Idea", "Assigned", "WIP", "UAT", "Completed", "Rejected"]

    cols = st.columns(len(statuses))

    for i, stage in enumerate(statuses):

        with cols[i]:

            st.markdown(f"### {stage}")

            stage_df = df[df["status"] == stage] if not df.empty else pd.DataFrame()

            for _, row in stage_df.iterrows():

                with st.expander(str(row.get("idea_name","No Idea Name"))):

                    st.write(f"👤 {row.get('name','-')}")
                    st.write(f"📌 {row.get('project','-')}")

                    new_status = st.selectbox(
                        "Move to",
                        statuses,
                        index=statuses.index(row["status"]),
                        key=f"kanban_{row['id']}"
                    )

                    if st.button("Update", key=f"btn_{row['id']}"):

                        update_idea(row["id"], {"status": new_status})
                        st.rerun()

    st.divider()

    # =========================================================
    # DETAILS TABLE
    # =========================================================
    st.subheader("Details Table")

    table_df = df.copy()

    cols = []

    for c in table_df.columns:
        cols.append(c)

        if c == "status":
            break

    table_df = table_df[cols]

    st.dataframe(table_df, use_container_width=True)

    

# =========================================================
# ADMIN
# =========================================================

elif menu == "Admin":

    st.subheader("Admin")

    with st.form("add"):

        email = st.text_input("Email")
        role_in = st.selectbox("Role", list(role_page_map.keys()))

        if st.form_submit_button("Add"):

            add_user(clean(email), clean(role_in))
            st.rerun()

    st.divider()

    for i, u in enumerate(load_permissions()):

        c1, c2, c3 = st.columns([4,3,2])

        with c1:
            st.write(u["email"])

        with c2:
            new_role = st.selectbox("Role", list(role_page_map.keys()), key=f"r_{i}")

        with c3:
            if st.button("Update", key=f"up_{i}"):
                update_role(clean(u["email"]), clean(new_role))
                st.rerun()

            if st.button("Delete", key=f"del_{i}"):
                delete_user(clean(u["email"]))
                st.rerun()
