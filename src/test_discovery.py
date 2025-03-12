#!/usr/bin/env python3
"""
Test script for simulating a discovery declaration for testing purposes.
"""
import os
import yaml
from loguru import logger

from agent import Agent
from utils import setup_logging

# Setup logging
setup_logging()

def load_config():
    """Load configuration from config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    """Run a simulation of a discovery being declared."""
    logger.info("Starting discovery simulation test")
    
    # Load configuration
    config = load_config()
    
    # Initialize the agent
    agent = Agent(config)
    
    # Sample discovery content
    discovery_content = """## The Quantum Gravitational Resonance Law

### Formal Statement
When quantum particles interact with gravitational fields at the Planck scale, they exhibit resonant frequency patterns that correlate with their mass distribution according to the formula:

$R_{qg} = \frac{G \cdot m \cdot f^2}{c^4} \cdot \Psi(r)$

Where:
- $R_{qg}$ is the Quantum Gravitational Resonance coefficient
- $G$ is the gravitational constant
- $m$ is the particle mass
- $f$ is the resonant frequency
- $c$ is the speed of light
- $\Psi(r)$ is a distance-dependent wave function

### Mathematical Formulation
The complete mathematical description incorporates a tensor field that describes the resonance across spacetime:

$T^{\mu\nu}_{qg} = \int R_{qg} \cdot \phi^{\mu\nu}(x) dx^4$

### Phenomena Explained
This law explains:
1. The apparent discrepancy between quantum field predictions and observed gravitational effects
2. Dark matter distribution patterns in galactic halos
3. Quantum coherence preservation in gravitational fields

### Predictions
The Quantum Gravitational Resonance Law predicts:
1. Specific frequency patterns in gravitational wave detections
2. A new class of quantum-gravitational phenomena observable at certain energy thresholds
3. Resolution of black hole information paradox through resonant information transfer

### Derivation Method
This law was derived through:
1. Analysis of anomalies in quantum field behavior near massive objects
2. Computer simulations of particle interactions at Planck scale
3. Mathematical reconciliation of quantum and relativistic frameworks
"""

    # Simulate a discovery declaration
    mock_response = f"""
### Progress Assessment
I have made significant breakthroughs in understanding quantum gravitational interactions.

### Next Action
I need to formalize my findings and verify the mathematical consistency.

### Execute Action
I performed extensive calculations and verified the consistency of my mathematical model.

### Outcome and Learning Report
The calculations confirmed my hypothesis and revealed a fundamental pattern.

### Learnings
I learned that quantum particles and gravitational fields interact in predictable patterns.

### Next Steps
Formalize the discovery and document all implications.

### DISCOVERY_DECLARATION
{discovery_content}
"""

    # Process the mock response
    agent._check_for_discovery(mock_response)
    
    # Check if findings.txt was created
    findings_file = "data/findings.txt"
    if os.path.exists(findings_file):
        logger.info(f"Success! Discovery was recorded to {findings_file}")
        # Display the first few lines
        with open(findings_file, "r") as f:
            first_lines = "".join(f.readlines()[:10])
            logger.info(f"Preview of findings.txt:\n{first_lines}...")
    else:
        logger.error(f"Failed to create {findings_file}")
    
    logger.info("Discovery simulation test completed")

if __name__ == "__main__":
    main() 