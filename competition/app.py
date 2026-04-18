"""
Robotic Chef Platform - Multi-Agent AI System
===============================================
Session 5: The Challenge - Agent-to-Agent (A2A) Integration

This Streamlit app integrates two AI agents:
- Agent 1: Food Analysis Agent (analyses dishes using Recipe MCP Server)
- Agent 2: Robotics Agent (designs robots using Robotics MCP Server)

All LLM calls go through llm_client (local LLM service via requests).

Run with:
    streamlit run app.py
"""

import streamlit as st
import asyncio
import os
from dotenv import load_dotenv

from agents import run_robotic_chef_pipeline
import llm_client

load_dotenv()

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Robotic Chef Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("How It Works")
    st.markdown(
        """
        This platform demonstrates **Agent-to-Agent (A2A)** communication
        between two specialised AI agents:

        **1. Food Analysis Agent**
        - Connects to the Recipe MCP Server
        - Analyses the dish: ingredients, techniques, equipment, safety
        - Produces a structured task specification

        **2. Robotics Designer Agent**
        - Receives the task specification from Agent 1
        - Connects to the Robotics MCP Server
        - Searches component databases
        - Designs a complete robotic cooking platform

        The output of Agent 1 flows directly into Agent 2 -- this is
        the A2A pattern in action.
        """
    )

    st.divider()
    st.header("Example Dishes to Try")
    st.markdown(
        """
        - Pasta Carbonara
        - Cheese Souffle
        - Sushi Rolls
        - Pizza Margherita
        - Beef Stir-Fry
        - Chocolate Cake
        - Fish and Chips
        - Pad Thai
        - French Omelette
        - Artisan Bread
        """
    )

    st.divider()
    st.caption(
        "AI Workshop - Session 5: The Challenge\n\n"
        "University of Hertfordshire"
    )

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.title("Robotic Chef Platform")
st.markdown("### Agent-to-Agent Multi-Agent System")
st.markdown(
    """
    Enter a dish name below and the system will:
    1. **Analyse** the dish using the Food Analysis Agent (Recipe MCP Server)
    2. **Design** a custom robotic platform using the Robotics Agent (Robotics MCP Server)

    The Food Analysis Agent's output is automatically passed to the Robotics Agent
    as a structured task specification -- demonstrating A2A communication.
    """
)

# ---------------------------------------------------------------------------
# Check for LLM service connectivity
# ---------------------------------------------------------------------------

llm_url = os.getenv("LLM_SERVICE_URL", "http://localhost:8000")
llm_token = os.getenv("LLM_API_TOKEN", "")

if not llm_token or llm_token == "your-token-here":
    st.warning(
        "**LLM API token not configured.** "
        "Please create a `.env` file in the session5 directory with:\n\n"
        "```\nLLM_SERVICE_URL=http://localhost:8000\nLLM_API_TOKEN=your-token\n```\n\n"
        "Or copy `.env.example` to `.env` and fill in your token."
    )

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

col1, col2 = st.columns([3, 1])

with col1:
    dish_name = st.text_input(
        "Dish name",
        value="pasta carbonara",
        placeholder="e.g. pasta carbonara, sushi rolls, chocolate cake...",
    )

st.markdown("#### Budget & Nutritional Constraints")
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    budget = st.slider("Total Budget (£)", 5.0, 100.0, 20.0, step=1.0, help="Total amount available for the whole meal.")
with c2:
    num_people = st.number_input("Number of People", 1, 10, 2, help="Number of servings required.")
with c3:
    priority = st.selectbox("Optimization Priority", ["Balance", "Cost", "Nutrition"])

with col2:
    run_button = st.button(
        "Design Robot Chef",
        type="primary",
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

if run_button and dish_name:
    priority_map = {
        "Balance": "Balance cost and nutrition equally.",
        "Cost": "Prioritise staying as far under budget as possible.",
        "Nutrition": "Prioritise high protein and vitamin content within budget.",
    }
    # Optimization priority (not yet passed to agent but good for future)
    priority_instruction = priority_map[priority]

    # Container for status updates
    status_container = st.status(
        f"Designing a robot chef for: **{dish_name}**", expanded=True
    )
    status_lines = []

    def status_callback(msg: str):
        """Callback to update the Streamlit status display."""
        status_lines.append(msg)
        with status_container:
            st.text(msg)

    # Run the async pipeline
    try:
        # Handle asyncio event loop for Streamlit compatibility
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If already in an async context (e.g. some Streamlit setups),
            # create a new loop in a thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run,
                    run_robotic_chef_pipeline(dish_name, budget, num_people, status_callback),
                ).result()
        else:
            result = asyncio.run(
                run_robotic_chef_pipeline(dish_name, budget, num_people, status_callback)
            )

        status_container.update(label="Pipeline complete!", state="complete", expanded=False)

        # Display results
        st.divider()
        
        # Financial & Nutritional Summary
        st.subheader("Financial & Nutritional Summary")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Budget", f"£{budget:.2f}")
        with m2:
            st.metric("Per Person", f"£{budget/num_people:.2f}")
        with m3:
            st.metric("Target Servings", num_people)

        st.info(f"**Optimization Focus:** {priority} – {priority_instruction}")

        # Agent 1 output
        with st.expander("Agent 1: Food Analysis", expanded=False):
            st.markdown(result["food_analysis"])

        # Agent 2 output
        with st.expander("Agent 2: Robot Design", expanded=False):
            st.markdown(result["robot_design"])

        # Agent 3 output
        with st.expander("Robot Cooking Sequence (Agent 3 Simulation)", expanded=True):
            st.markdown(result["cooking_simulation"])

    except Exception as e:
        status_container.update(label="Pipeline failed", state="error")
        st.error(f"An error occurred: {e}")
        st.exception(e)

elif run_button and not dish_name:
    st.warning("Please enter a dish name to get started.")
