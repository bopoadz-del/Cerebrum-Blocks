"""
Validated system configurations for MSSDPPG based on the official rubric.

Only these systems are real:
- 20 ft standalone container
- 4×40 ft symmetric system
- 4×40 ft asymmetric system
- Mega pendulum

Each configuration includes arm lengths, fixed masses, number of pendulums,
expected power at rated wind speed, and total cost.  Helper functions for
mass and generator scaling are provided.
"""

CONFIGS = {
    '20ft_standalone': {
        'name': '20ft Standalone Container',
        'L1': 0.68,  # m
        'L2': 1.50,  # m (ratio ≈ 1:2.2)
        'pendulums': 12,
        'm_middle': 30,
        'm_tip': 5,
        'expected_power': 1.58,  # kW @ 6 m/s
        'cost': 12000,
        'module_area_m2': 29.7,  # footprint ≈ 12 m × 2.4 m
    },
    '4x40ft_symmetric': {
        'name': '4×40ft Container System (Symmetric)',
        'L1': 2.00,
        'L2': 2.00,
        'pendulums': 48,
        'm_middle': 30,
        'm_tip': 5,
        'expected_power': 4.50,  # kW @ 6 m/s
        'cost': 36000,
        'module_area_m2': 57.6,  # two 40 ft containers: 12 m × 4.8 m
    },
    '4x40ft_asymmetric': {
        'name': '4×40ft Container System (Asymmetric)',
        'L1': 1.31,
        'L2': 2.88,
        'pendulums': 48,
        'm_middle': 30,
        'm_tip': 5,
        'expected_power': 14.90,  # kW @ 6 m/s
        'cost': 47000,
        'module_area_m2': 57.6,
    },
    'mega': {
        'name': 'Mega-Pendulum (Asymmetric)',
        'L1': 4.38,
        'L2': 9.63,
        'pendulums': 24,
        'm_middle': 120,
        'm_tip': 30,
        'expected_power': 93.0,  # kW @ 8 m/s
        'cost': 240000,
        'module_area_m2': 100.0,  # approximate site footprint
    },
}

def calculate_arm_masses(L1: float, L2: float, m_upper_base: float = 25, m_lower_base: float = 20) -> tuple[float, float]:
    """
    Scale the distributed arm masses for upper and lower arms based on a 2 m reference.
    m_upper = m_upper_base × (L1 / 2)²
    m_lower = m_lower_base × (L2 / 2)²
    """
    m_upper = m_upper_base * (L1 / 2.0) ** 2
    m_lower = m_lower_base * (L2 / 2.0) ** 2
    return m_upper, m_lower

def calculate_scaled_kt(k_t_base: float, L: float, L_ref: float = 2.0) -> float:
    """
    Scale generator torque constant by the square of arm length relative to a reference.
    k_t_scaled = k_t_base × (L / L_ref)²
    """
    return k_t_base * (L / L_ref) ** 2
