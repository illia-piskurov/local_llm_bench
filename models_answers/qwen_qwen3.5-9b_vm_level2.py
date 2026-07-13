def run(program: str) -> list[str]:
    stack = []
    output = []
    
    # Parse lines into instructions and labels
    # Each instruction stores original line number for error reporting
    instructions = [] 
    labels = {}       # Map label name to instruction index
    
    lines = program.splitlines()
    
    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue
