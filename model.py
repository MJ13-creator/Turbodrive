import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_echarts import st_echarts
import uuid
import os
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
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="EFS Turbo Drive", layout="wide")

# =========================================================
# CLEAN FUNCTION
# =========================================================
def clean(x):

    if pd.isna(x):
        return None

    x = str(x).replace("\u00a0", "")
    x = x.strip().lower()
    x = re.sub(r"\s+", " ", x)

    return x


# =========================================================
# SAFE DATA CLEANER
# =========================================================
def clean_df(df):

    df = df.copy()

    for col in [
        "idea",
        "idea_name",
        "status",
        "rejection_reason",
        "name",
        "project",
        "category"
    ]:

        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    if "roi" in df.columns:
        df["roi"] = pd.to_numeric(
            df["roi"],
            errors="coerce"
        ).fillna(0)

    return df


# =========================================================
# LOAD PERMISSIONS
# =========================================================
permission_data = load_permissions()

# normalize safely
permission_data = permission_data or []

for u in permission_data:
    u["email"] = clean(u.get("email", ""))
    u["role"] = clean(u.get("role", ""))

user_df = pd.DataFrame(permission_data)

email_role_map = {
    u["email"]: u["role"]
    for u in permission_data
    if u.get("email") and u.get("role")
}
# =========================================================
# ROLE ACCESS
# =========================================================
role_page_map = {

    "super user": [
        "Submit Idea",
        "PL Assignment",
        "Feasibility",
        "Approval",
        "Dashboard",
        "Admin"
    ],

    "normal user": [
        "Submit Idea"
    ],

    "automation engineer": [
        "Submit Idea",
        "Feasibility",
        "Dashboard"
    ],

    "automation pl": [
        "Submit Idea",
        "PL Assignment",
        "Feasibility",
        "Approval",
        "Dashboard"
    ],

    "pl/spl": [
        "Submit Idea",
        "Approval",
        "Dashboard"
    ]
}

# =========================================================
# HEADER
# =========================================================
st.markdown(
    "<h1 style='text-align:center;'>EFS TURBO DRIVE</h1>",
    unsafe_allow_html=True
)

# =========================================================
# LOGIN
# =========================================================
st.sidebar.title("Login")

email_input = st.sidebar.text_input("Enter Email ID")

user_email = clean(email_input)

role = email_role_map.get(clean(user_email))

# =========================================================
# AUTH
# =========================================================
if not user_email:
    st.warning("Please enter email")
    st.stop()

if role is None:
    st.error("🚫 Access Denied")
    st.stop()

if role:
    st.sidebar.success(f"Role: {role.title()}")
else:
    st.error("Role not found in system")
    st.stop()

allowed_pages = role_page_map.get(role, [])

if not allowed_pages:
    st.error("No pages assigned")
    st.stop()

menu = st.sidebar.selectbox(
    "Menu",
    allowed_pages
)

# =========================================================
# SUBMIT IDEA
# =========================================================
if menu == "Submit Idea":

    st.subheader("Submit Idea")

    pl_users = [
        u["email"]
        for u in permission_data
        if u.get("role") in ["pl/spl", "automation pl"]
    ]

    pl_users = sorted(list(set(pl_users)))

    with st.form("submit_form"):

        name = st.text_input("Idea submitter name")
        idea_name = st.text_input("Idea Name")
        idea = st.text_area("Idea")

        project = st.selectbox(
            "Project",
            ["CA-MRO","BA-MRO","BA-LCE","CA-LCE","Controls","Technical Response"]
        )

        category = st.selectbox(
            "Type",
            ["Customer Requirement","Internal"]
        )

        pl_name = st.selectbox(
            "PL / SPL Name",
            pl_users
        )

        # ✅ MUST be INSIDE form
        submit = st.form_submit_button("Submit")

    # ✅ OUTSIDE form
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

        st.success("Idea Submitted Successfully ✅")
        st.rerun()

# =========================================================
# PL ASSIGNMENT
# =========================================================
elif menu == "PL Assignment":

    st.subheader("Assign Engineer")

    data = get_all()
    df = clean_df(pd.DataFrame(data if data else []))

    # =====================================================
    # AUTOMATION ENGINEERS
    # =====================================================
    engineer_users = [
        u["email"]
        for u in permission_data
        if u.get("role") == "automation engineer"
    ]

    engineer_users = sorted(list(set(engineer_users)))

    for item in df.to_dict("records"):

        if item.get("status") == "New Idea":

            st.markdown(
                f"""
                <div style="
                    padding:10px;
                    background:#F6F8FB;
                    border-radius:10px;
                    border-left:4px solid #3B82F6;
                    margin-bottom:10px;
                    font-size:16px;
                    font-weight:500;">
                    💡 {item.get('idea','No Idea')}
                </div>
                """,
                unsafe_allow_html=True
            )

            eng = st.selectbox(
                "Engineer",
                engineer_users,
                key=f"eng_{item['id']}"
            )

            if st.button("Assign", key=f"assign_{item['id']}"):

                update_idea(
                    item["id"],
                    {
                        "assigned_engineer": eng,
                        "status": "Assigned",
                        "assigned_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                )

                st.success("Moved to next stage")
                st.rerun()

# =========================================================
# FEASIBILITY
# =========================================================
elif menu == "Feasibility":

    st.subheader("Feasibility Study")

    df = clean_df(pd.DataFrame(get_all()))

    for item in df.to_dict("records"):

        if item["status"] == "Assigned":

            st.markdown(f"### 💡 {item.get('idea','No Idea')}")

            st.write(
                f"👷 Engineer: {item.get('assigned_engineer','-')}"
            )

            st.write(
                f"🧑‍💼 PL / SPL: {item.get('pl_name','-')}"
            )

            st.write(
                f"🧑‍💼 Idea Submitter Name: {item.get('name','-')}"
            )

            manual = st.number_input(
                "Manual Effort",
                key=f"m_{item['id']}"
            )

            fte = st.number_input(
                "FTE",
                key=f"f_{item['id']}"
            )

            eng = st.number_input(
                "Automation Effort",
                key=f"e_{item['id']}"
            )

            freq = st.selectbox(
                "Frequency",
                ["Daily", "Weekly", "Monthly", "Yearly"],
                key=f"fr_{item['id']}"
            )

            multiplier = {
                "Daily": 260,
                "Weekly": 52,
                "Monthly": 12,
                "Yearly": 1
            }

            roi = (
                manual * fte * multiplier[freq]
            ) / (eng if eng else 1)

            st.info(f"ROI: {round(roi,2)}")

            comments = st.text_area(
                "Comments",
                key=f"comm_{item['id']}"
            )

            meeting_link = "https://outlook.office.com/calendar/0/deeplink/compose"

            st.link_button(
                "📅 Setup Outlook Meeting",
                meeting_link,
                key=f"meet_{item['id']}"
            )

            if st.button("Submit", key=f"feas_{item['id']}"):

                update_idea(item["id"], {

                    "status": "WIP",

                    "roi": roi,

                    "feasibility_comments": comments,

                    "feasibility_data": {
                        "manual": manual,
                        "fte": fte,
                        "eng": eng,
                        "freq": freq,
                    },

                    "wip_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

                st.success("Moved to next stage")

# =========================================================
# APPROVAL
# =========================================================
elif menu == "Approval":

    st.subheader("PL / SPL Approval")

    df = clean_df(pd.DataFrame(get_all()))

    pl_list = sorted(
        df["pl_name"].dropna().unique().tolist()
    )

    pl_user = st.selectbox(
        "Select PL / SPL Name",
        [""] + pl_list
    )

    if not pl_user:
        st.stop()

    data = df[
        (df["status"] == "WIP") &
        (df["pl_name"] == pl_user)
    ].to_dict("records")

    for item in data:

        st.markdown(f"### 💡 {item['idea']}")

        fd = item.get("feasibility_data", {})

        st.table(pd.DataFrame([{
            "Manual Effort": fd.get("manual", ""),
            "FTE": fd.get("fte", ""),
            "Automation Effort": fd.get("eng", ""),
            "Frequency": fd.get("freq", ""),
            "ROI": item.get("roi", 0)
        }]))

        decision = st.radio(
            "Decision",
            ["GO", "NO-GO"],
            key=f"d_{item['id']}"
        )

        comment = st.text_area(
            "Comments *",
            key=f"c_{item['id']}"
        )

        reason = None

        if decision == "NO-GO":

            reason = st.selectbox(
                "Reason",
                [
                    "Technical Rejection",
                    "Business Rejection"
                ],
                key=f"r_{item['id']}"
            )

        if st.button("Submit", key=f"appr_{item['id']}"):

            if not comment.strip():
                st.error("Comments are mandatory")
                st.stop()

            new_status = (
                "UAT"
                if decision == "GO"
                else "Rejected"
            )

            update_data = {

                "status": new_status,
                "decision": decision,
                "rejection_reason": reason,
                "approval_comment": comment
            }

            now = datetime.now().strftime("%Y-%m-%d %H:%M")

            if new_status == "UAT":
                update_data["uat_date"] = now
            else:
                update_data["completion_date"] = now

            update_idea(item["id"], update_data)

            st.success("Moved to next stage")

# =========================================================
# DASHBOARD
# =========================================================
elif menu == "Dashboard":
   import pandas as pd
   from streamlit_echarts import st_echarts
   st.markdown("""
<h2>📊 Dashboard</h2>
   """, unsafe_allow_html=True)
   # =========================================================
   # DATA LOAD
   # =========================================================
   df = pd.DataFrame(get_all())
   if df.empty:
       st.warning("No ideas available")
       st.stop()
   df = df.copy()
   # =========================================================
   # CLEANING
   # =========================================================
   df["status"] = df["status"].fillna("New Idea")
   df["category"] = df["category"].fillna("")
   df["rejection_reason"] = df["rejection_reason"].fillna("")
   df["roi"] = pd.to_numeric(df["roi"], errors="coerce").fillna(0)
   # =========================================================
   # KPI METRICS
   # =========================================================
   total_roi_customer = round(
       df[df["category"] == "Customer Requirement"]["roi"].sum(),
       2
   )
   total_roi_internal = round(
       df[df["category"] == "Internal"]["roi"].sum(),
       2
   )
   total_ideas = len(df)
   total_completed = len(df[df["status"] == "Completed"])
   c1, c2, c3, c4 = st.columns(4)
   with c1:
       st.metric("Total Ideas", total_ideas)
   with c2:
       st.metric("Completed", total_completed)
   with c3:
       st.metric("Customer ROI", total_roi_customer)
   with c4:
       st.metric("Internal ROI", total_roi_internal)
   st.divider()
   st.markdown(" 🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️")
   # =========================================================
   # TREE SECTION
   # =========================================================
   st.subheader("Ideation Workflow Tree")
   # =========================================================
   # HELPERS
   # =========================================================
   def count(d, status):
       return len(d[d["status"] == status])
   def reject(d, reason):
       return len(
           d[
               (d["status"] == "Rejected") &
               (d["rejection_reason"] == reason)
           ]
       )
   # =========================================================
   # COLORS
   # =========================================================
   blue_node = {
       "backgroundColor": "#2563EB",
       "color": "#FFFFFF",
       "borderColor": "#60A5FA"
   }
   green_node = {
       "backgroundColor": "#16A34A",
       "color": "#FFFFFF",
       "borderColor": "#4ADE80"
   }
   orange_node = {
       "backgroundColor": "#EA580C",
       "color": "#FFFFFF",
       "borderColor": "#FDBA74"
   }
   # =========================================================
   # TREE DATA
   # =========================================================
   tree = {
       "name": f"Ideation ({len(df)})",
       "label": orange_node,
       "children": [
           {
               "name": f"Triaged / Feasibility ({count(df,'Assigned')})",
               "label": blue_node,
               "children": [
                   # =================================================
                   # ACCEPTED
                   # =================================================
                   {
                       "name": (
                           f"Accepted ("
                           f"{count(df,'WIP') + count(df,'UAT') + count(df,'Completed')}"
                           f")"
                       ),
                       "label": green_node,
                       "children": [
                           # =========================================
                           # CUSTOMER
                           # =========================================
                           {
                               "name": (
                                   f"Customer ("
                                   f"{len(df[df['category']=='Customer Requirement'])}"
                                   f")"
                               ),
                               "label": green_node,
                               "children": [
                                   {
                                       "name": (
                                           f"WIP ("
                                           f"{len(df[(df['category']=='Customer Requirement') & (df['status']=='WIP')])}"
                                           f")"
                                       ),
                                       "label": green_node
                                   },
                                   {
                                       "name": (
                                           f"UAT ("
                                           f"{len(df[(df['category']=='Customer Requirement') & (df['status']=='UAT')])}"
                                           f")"
                                       ),
                                       "label": green_node
                                   },
                                   {
                                       "name": (
                                           f"Deployed ("
                                           f"{len(df[(df['category']=='Customer Requirement') & (df['status']=='Completed')])}"
                                           f")"
                                       ),
                                       "label": green_node
                                   }
                               ]
                           },
                           # =========================================
                           # INTERNAL
                           # =========================================
                           {
                               "name": (
                                   f"Internal ("
                                   f"{len(df[df['category']=='Internal'])}"
                                   f")"
                               ),
                               "label": green_node,
                               "children": [
                                   {
                                       "name": (
                                           f"WIP ("
                                           f"{len(df[(df['category']=='Internal') & (df['status']=='WIP')])}"
                                           f")"
                                       ),
                                       "label": green_node
                                   },
                                   {
                                       "name": (
                                           f"UAT ("
                                           f"{len(df[(df['category']=='Internal') & (df['status']=='UAT')])}"
                                           f")"
                                       ),
                                       "label": green_node
                                   },
                                   {
                                       "name": (
                                           f"Deployed ("
                                           f"{len(df[(df['category']=='Internal') & (df['status']=='Completed')])}"
                                           f")"
                                       ),
                                       "label": green_node
                                   }
                               ]
                           }
                       ]
                   },
                   # =================================================
                   # REJECTED
                   # =================================================
                   {
                       "name": f"Rejected ({count(df,'Rejected')})",
                       "label": green_node,
                       "children": [
                           {
                               "name": (
                                   f"Technical ("
                                   f"{reject(df,'Technical Rejection')}"
                                   f")"
                               ),
                               "label": green_node
                           },
                           {
                               "name": (
                                   f"Business ("
                                   f"{reject(df,'Business Rejection')}"
                                   f")"
                               ),
                               "label": green_node
                           }
                       ]
                   }
               ]
           }
       ]
   }
   # =========================================================
   # ECHART OPTION
   # =========================================================
   option = {
       "backgroundColor": "#0B0B0D",
       "tooltip": {
           "trigger": "item",
           "triggerOn": "mousemove"
       },
       "series": [
           {
               "type": "tree",
               "data": [tree],
               "symbol": "roundRect",
               "orient": "LR",
               "expandAndCollapse": True,
               "initialTreeDepth": -1,
               "top": "5%",
               "bottom": "5%",
               "left": "15%",
               "right": "20%",
               "layerPadding": 120,
               "nodePadding": 40,
               "lineStyle": {
                   "color": "#FF6A00",
                   "width": 2
               },
               "label": {
                   "color": "#FFFFFF",
                   "fontSize": 11,
                   "fontWeight": "bold",
                   "backgroundColor": "#1E1E24",
                   "borderColor": "#FF6A00",
                   "borderWidth": 2,
                   "borderRadius": 6,
                   "padding": [7, 12],
                   "width": 190,
                   "lineHeight": 18,
                   "overflow": "break",
                   "distance": 60,
                   "formatter": "{b}"
               },
               "leaves": {
                   "label": {
                       "width": 180,
                       "overflow": "break"
                   }
               },
               "emphasis": {
                   "focus": "descendant",
                   "label": {
                       "backgroundColor": "#FF6A00",
                       "color": "#000000"
                   }
               }
           }
       ]
   }
   st_echarts(
       option,
       height="750px",
       width="109%"
   )
   st.divider()
   st.markdown(" 🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️")
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
                        st.markdown(" 🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️🏎️")
   # =========================================================
   # DETAILS TABLE
   # =========================================================
   st.subheader("Details Table")
   table_df = df.copy()
   cols_to_show = []
   for c in table_df.columns:
       cols_to_show.append(c)
       if c == "status":
           break
   table_df = table_df[cols_to_show]
   st.dataframe(
       table_df,
       use_container_width=True
   )
   # =========================================================
   # DOWNLOAD BUTTON
   # =========================================================
   csv = table_df.to_csv(index=False).encode("utf-8")
   st.download_button(
       "Download CSV",
       csv,
       "ideation_dashboard.csv",
       "text/csv"
   )
# =========================================================
# ADMIN
# =========================================================
elif menu == "Admin":

    st.subheader("Admin Panel")

    permission_data = load_permissions()

    # =====================================================
    # ADD USER
    # =====================================================
    st.markdown("### Add User")

    with st.form("add_user"):

        new_email = st.text_input("Email")

        new_role = st.selectbox(
            "Role",
            [
                "super user",
                "normal user",
                "automation engineer",
                "automation pl",
                "pl/spl"
            ]
        )

        submitted = st.form_submit_button("Add User")

    if submitted:

        if new_email.strip() == "":

            st.error("Email required")

        else:

            add_user(
                clean(new_email),
                clean(new_role)
            )

            st.success("User Added")

            st.rerun()

    st.divider()

    # =====================================================
    # EXISTING USERS
    # =====================================================
    st.markdown("### Existing Users")

    permission_data = load_permissions()

    roles = [
        "super user",
        "normal user",
        "automation engineer",
        "automation pl",
        "pl/spl"
    ]

    for i, user in enumerate(permission_data):

        st.markdown("---")

        c1, c2, c3 = st.columns([4, 3, 2])

        email = clean(user["email"])
        role = clean(user["role"])

        with c1:
            st.write(email)

        with c2:

            updated_role = st.selectbox(
                "Role",
                roles,
                index=roles.index(role)
                if role in roles else 0,
                key=f"role_{i}_{email}"
            )

        with c3:

            if st.button(
                "Update",
                key=f"upd_{i}_{email}"
            ):

                update_role(
                    clean(email),
                    clean(updated_role)
                )

                st.success(f"Updated {email}")

                st.rerun()

            if st.button(
                "Delete",
                key=f"del_{i}_{email}"
            ):

                delete_user(clean(email))

                st.warning(f"Deleted {email}")

                st.rerun()
