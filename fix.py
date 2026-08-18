import random, math

random.seed(42)

# Find and fix float -> int issues in the cover script
with open("cover_减少依赖_deluxe.py", "r") as f:
    content = f.read()

# Fix alpha calculations that produce floats
# In _draw_unity_mandala: alpha = 60 + 40 * (1 - abs(mult - 0.5) * 2)
old = """        alpha = 60 + 40 * (1 - abs(mult - 0.5) * 2)"""
new = """        alpha = int(60 + 40 * (1 - abs(mult - 0.5) * 2))"""
content = content.replace(old, new)

# In _radial_glow: a = int(alpha * (1 - ratio)) - this is fine already
# In _soft_circle: a = int(alpha * (1 - ratio) * ratio) - fine
# In _draw_converge_paths: a = int(20 * (1 - ratio) * (1 - ratio)) - fine

# Fix width calculation to ensure int
old = """width = max(1, int((1.5 + 0.8 * (1 - mult)) * s))"""
new = """width = int(max(1, (1.5 + 0.8 * (1 - mult)) * s))"""
content = content.replace(old, new)

with open("cover_减少依赖_deluxe.py", "w") as f:
    f.write(content)

print("✅ Fixed float alpha values")
