flowchart TB
  %% =========================
  %% STRUCTURAL INTELLIGENCE SYSTEM MAP
  %% =========================

  A[Structural Intelligence (SI)\n\"Organization of form under pressure\"]:::core

  %% --- Main planes
  A --> B[Epistemic Integrity Plane\n(Coherence ↔ Contact)]:::plane
  A --> C[Agency & Worth Plane\n(Reward-pressure ↔ Sovereignty)]:::plane
  A --> D[Load & Repair Plane\n(Truth-load ↔ Containment)]:::plane
  A --> E[Civilizational Plane\n(Standardization ↔ Answerability)]:::plane
  A --> F[Psyche Interface Plane\n(Persona ↔ Shadow)]:::plane

  %% --- Epistemic Integrity
  B --> B1[Coherence]:::node
  B --> B2[Contact\n(Answerability to constraint)]:::node
  B --> B3[Coherence-Contact Gap]:::key
  B --> B4[Resonance\n(\"felt right\" signal)]:::node
  B --> B5[Tethering\n(bind coherence to constraint)]:::key
  B --> B6[Coherence-Theater]:::risk
  B --> B7[Hallucination Regime\n(coherence becomes currency)]:::risk

  %% --- Agency & Worth
  C --> C1[Reward-pressure]:::node
  C --> C2[Variable Worth\n(worth priced by signals)]:::risk
  C --> C3[Pricing Self]:::risk
  C --> C4[Self-sale\n(trade answerability for valuation)]:::risk
  C --> C5[Reflex Agency\n(signal-optimized output)]:::risk
  C --> C6[Invariance Constraint\n(non-tradable baseline)]:::key
  C --> C7[Fixed Worth\n(invariant worth)]:::key
  C --> C8[Sovereignty\n(non-tradability in agency)]:::key

  %% --- Load & Repair
  D --> D1[Truth-load\n(what can be carried)]:::key
  D --> D2[Truth as Load\n(integrability over correctness)]:::key
  D --> D3[Presence\n(alignment under constraint)]:::node
  D --> D4[Containment\n(hold activation without collapse)]:::key
  D --> D5[Collapse\n(forced contact event)]:::node
  D --> D6[Repair\n(revision that preserves answerability)]:::key
  D --> D7[Orientation\n(minimum livable frame)]:::node
  D --> D8[Cheap Coherence\n(low-cost completion)]:::risk

  %% --- Civilizational
  E --> E1[Standardization\n(legibility via metrics)]:::node
  E --> E2[Grid\n(comparability frame)]:::node
  E --> E3[Thinning of Answerability]:::risk
  E --> E4[Consequence\n(who pays over time)]:::key
  E --> E5[Structural Audit\n(failure reveals incentives)]:::key

  %% --- Psyche interface
  F --> F1[Persona\n(social interface)]:::node
  F --> F2[Shadow\n(disowned agency)]:::node
  F --> F3[Personality Trap\n(personality as coherence engine)]:::risk
  F --> F4[Projection / Moralization / Compulsion]:::risk

  %% --- Cross-links (the real engine)
  B3 --> D6
  B5 --> D6
  C1 --> C5
  C2 --> C4
  C6 --> C8
  D1 --> D5
  D4 --> D3
  E2 --> C1
  E1 --> B7
  F1 --> B6
  F3 --> B7
  D8 --> B7

  classDef core fill:#111,stroke:#111,color:#fff;
  classDef plane fill:#f2f2f2,stroke:#bbb,color:#111;
  classDef node fill:#fff,stroke:#999,color:#111;
  classDef key fill:#e8f3ff,stroke:#4a90e2,color:#111;
  classDef risk fill:#ffecec,stroke:#e24a4a,color:#111;
