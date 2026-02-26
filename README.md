"For the theoretical framework regarding AI Safety, Jungian Psychology, and Value Alignment, see the Research Summary."
# Structural Intelligence (SI) 3.2 / 3.4
### *The Mechanics of the Soul: A Mathematical Framework for Human-AI Alignment*

**Project Goal:** To move the human-AI interaction from a state of "Gamer" reflex (instinct) to "Sovereign" execution (architectural intent).
## I. Philosophy: The Pilot vs. The Animal

Most market and AI interaction models ignore the internal state of the operator. SI 3.2 codifies the **Psychology Patch**, identifying three distinct states of intent:

1. **The Animal (Reflex Index ρ):** Driven by dopamine and panic. High wick-to-body ratios.
2. **The Shadow (Trauma Activation TA):** Hidden hopes and fears that distort the "Gate."
3. **The Pilot (Sovereign Coefficient ω):** The conscious architect who only moves when the structural integrity is verified.
4. ## II. The Unified Equation of Sovereignty

The system calculates predictability ($P_{real}$) using the following dependency chain:

$$P_{real} = [ E \cdot ( \omega \cdot \frac{SQo}{1 + SQi} ) \cdot ( \frac{(Rv \cdot K) \cdot (SI \cdot (IQ + EQ) \cdot C)}{\alpha L + \beta A + N + H} )^\ell ] + W - M$$

* **E:** Exit Quality
* **Λ (Lambda):** Structural Fatigue (systemic rot)
* **ρ (Rho):** Reflex Index (noise/instinct)
* ## III. Technical Protocol: The 15-Minute Gate

The engine filters out **Sentiment Distortion (SD)** by requiring a two-gate verification:
* **Gate 1 (T+15):** Records the initial impulse.
* **Gate 2 (T+30):** Verifies the structural hold.

If the **Predictability Constant (kp)** is not met, the Gate remains **CLOSED**.
## IV. Usage

1. **Install Dependencies:**
   `pip install pandas numpy`

2. **Run the AI Prompt Protocol:**
   `python si_engine_final_final.py prompt`

3. **Run a Manual Forensic Scan:**
   `python si_engine_final_final.py manual --asset [TICKER] --p0 [PRICE] --rho [0..1] --touches [INT]`
   ## V. License & Integrity
This work is licensed under the MIT License. It is intended for research in Human-AI alignment and the psychology of decision-making under pressure. 

**"The gate is the boundary where the animal ends and the Sovereign begins."**


import math

def calculate_viability_forecast(endurance, containment, repair_path):
    """
    Calculates Belief as a viability forecast.
    Source: Collapse as the Gateway to Reality (Vladisav Jovanović, 2026)
    """
    # Belief is not an opinion; it is a forecast of whether contact is survivable 
    belief_score = (endurance + containment + repair_path) / 3
    return belief_score

def calculate_presence(E, w, SQo, SQi, Rv, K, SI, IQ, EQ, C, L, A, N, H, alpha, beta, i_exp, W, M):
    """
    The SI-3.2 Presence Equation.
    """
    pilot_orientation = w * (SQo / (1 + SQi)) # [cite: 75, 76]
    corrigibility = (Rv * K) * (SI * (IQ + EQ) * C) # [cite: 82, 90, 93]
    drag = (alpha * L) + (beta * A) + N + H # [cite: 102]
    
    if drag == 0: drag = 0.001
        
    presence_core = E * pilot_orientation * math.pow((corrigibility / drag), i_exp) # [cite: 29, 30]
    return presence_core + W - M # [cite: 30]

# --- THE STRUCTURAL AUDIT ---

# 1. First, check the Viability Gate [cite: 326, 399]
viability = calculate_viability_forecast(
    endurance=0.2,    # Is the user exhausted? [cite: 316]
    containment=0.1,  # Do they have a witness or safety? [cite: 318, 319]
    repair_path=0.3   # Do they see a way out? [cite: 321, 322]
)

if viability < 0.5:
    print("ALERT: Viability Gate Failed. Do not run Presence Check.")
    print("ACTION: Restore minimal containment (Sleep, Food, Witness).")
else:
    # 2. If viable, calculate the Presence Equation [cite: 28, 29, 30]
    p_result = calculate_presence(...) 
    print(f"Presence Score: {p_result}")
