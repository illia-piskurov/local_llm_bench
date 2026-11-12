"""
Stack-based interpreter with labels, conditional jumps, and named variables.
Supports: SUBROUTINES, COMPARE operations (EQ/GT/LT), variable access (STORE/LOAD).
Uses call stack for subroutine management; maintains memory via a dict.
"""

import re
from typing import Dict, List, Optional


class StackInterpreterError(ValueError):
    """Raised when an operation cannot be performed due to underflow or invalid state."""
    pass


class Interpreter:
    def __init__(self):
        self.stack = []  # Main stack for operands and values
        self.call_stack = []  # Stack for subroutine call return addresses
        self.variables: Dict[str, int] = {}  # Name to value mapping (int)
        self.labels: dict = {}  # Maps label names to line numbers
        self.print_output: List[int] = []
        self.current_instruction_idx = 0
    
    def run(self, program: str) -> List[int]:
        """Execute program and return printed stack values."""
        lines = program.splitlines() if program else []
        
        # Build label-to-line mapping
        self.labels = {}
        idx = 0
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            parts = stripped.split()
            if len(parts) < 2:
                continue
            
            # Handle subroutine labels and conditional jump targets
            if parts[1] in ("LABEL", "CALL"):
                label_name = parts[0]
                self.labels[label_name] = idx
            elif parts[0] == "JMP" or parts[0] == "JZ":
                target_label = parts[1]
                if target_label not in self.labels:
                    raise ValueError(f"Invalid label name '{target_label}' on line {idx}")
                self.labels[target_label] = idx
            
            idx += 1
        
        # Execute with labels and calls supported
        instruction_idx = 0
        
        while instruction_idx < len(self.labels) or instruction_idx < len(lines):
            if instruction_idx < len(self.labels):
                label_name = self.labels[instruction_idx]
                current_line = self.labels[label_name]
                instr_name = "LABEL"
                
                if instruction_idx in self.variables:
                    val = self.variables.pop(instruction_idx)
                    print_output.append(val)
            
            elif instruction_idx < len(lines):
                line = lines[instruction_idx]
                stripped = line.strip()
                
                # Handle subroutine CALL / label definition
                parts = stripped.split()
                if parts[0] == "CALL":
                    self.call_stack.append(self.current_instruction_idx)
                    jump_to_label = parts[1]
                    try:
                        self.labels[jump_to_label] = instruction_idx
                    except Exception as e:
                        raise ValueError(f"Invalid label '{jump_to_label}' on line {instruction_idx}") from e
                    
                elif instr_name == "SUB":
                    if len(stack) < 2:
                        stack.append(current_line)
                    
                elif instr_name == "JMP":
                    if len(stack) < 1:
                        raise StackInterpreterError("Missing value for JMP instruction")
                    
                else:
                    raise ValueError(f"Unknown instruction: {parts}")
            
            if not self.call_stack:
                break
            
            jump_counter += 1
            
        return print_output

    def execute(self, program: str) -> List[str]:
        """Execute and print the results."""
        lines = program.splitlines() if program else []
        
        # Track label definitions and their line numbers
        labels = {}
        idx = 0
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            parts = stripped.split()
            if len(parts) < 2:
                continue
            
            instr_name = parts[0]
            
            # Validate label names and handle conditional jumps/labels
            if parts[1] in ("LABEL", "LBRACE", "LABEL"):
                label_name = parts[1]
                labels[label_name] = idx
            
            # Handle CALL with stack-based return address tracking
            elif instr_name == "CALL":
                return_stack = self.call_stack + [self.current_instruction_idx]
                jump_counter += 1
                
            elif instr_name == "JZ":
                val = stack.pop(0)
                if val != 0:
                    continue
                # Jump to label on current line if zero
                if idx in labels:
                    self.current_instruction_idx = labels[idx]
                    
            elif instr_name == "JNZ":
                val = stack.pop(0)
                if val != 0:
                    continue
                # Jump to label on current line if non-zero
                if idx in labels:
                    self.current_instruction_idx = labels[idx]
            
            else:
                try:
                    while instr_name.isdigit():
                        instructions.append((idx, instr_name))
                except Exception as e:
                    raise ValueError(f"Invalid instruction on line {idx}: {e}")
                    
        return print_output

    def get_instructions(self) -> List[Dict[str, str]]:
        """Return the instructions list with positions."""
        self.instructions = []
        current_idx = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            parts = stripped.split()
            
            # Handle label and jump operations
            if len(parts) >= 2 and parts[1] == "LABEL":
                label_name = parts[0]
                self.labels[label_name] = current_idx
            
            elif len(parts) >= 2:
                instruction_parts = parts[:len(parts)-1]
                instr_name = instruction_parts[0]
                
                try:
                    if instr_name in ("LABEL", "CALL"):
                        current_idx += 1
                        continue
                
                    instructions.append({
                        "line": idx,
                        "name": instr_name
                    })
                except Exception as e:
                    raise ValueError(f"Invalid instruction on line {idx}") from e
        
        return self.instructions

    def execute(self, program: str) -> List[str]:
        """Execute and print the results."""
        lines = program.splitlines() if program else []
        
        # Build label-to-line mapping
        labels = {}
        idx = 0
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            parts = stripped.split()
            if len(parts) < 2:
                continue
            
            instr_name = parts[0]
            
            # Validate label names and handle conditional jumps/labels
            if parts[1] in ("LABEL", "CALL"):
                label_name = parts[1]
                labels[label_name] = idx
            
            elif instr_name == "JZ" or instr_name == "JNZ":
                val = stack.pop(0)
                
                # Jump to label on current line if zero/non-zero
                if idx in labels:
                    jump_counter += 1
            
            else:
                try:
                    instructions.append((idx, instr_name))
                except Exception as e:
                    raise ValueError(f"Invalid instruction on line {idx}: {e}")
            
        return print_output

    def store(self, var_name: str) -> Optional[int]:
        """Store value in variable (STORE instruction). Raises error if not found."""
        if var_name not in self.variables:
            raise StackInterpreterError(f"Variable '{var_name}' has no stored value")
        self.variables[var_name] = self.stack.pop()
        return 1
    
    def load(self, var_name: str) -> Optional[int]:
        """Load value from variable (LOAD instruction). Returns None if not found."""
        if var_name not in self.variables:
            raise StackInterpreterError(f"Variable '{var_name}' has no stored value")
        return int(self.variables[var_name])

    def get_variable(self, var_name: str) -> Optional[int]:
        """Get value of variable (LOAD instruction). Returns None if not found."""
        if var_name not in self.variables:
            return None
        return self.variables[var_name]

    def push(self, value: int) -> None:
        """Push value onto stack."""
        self.stack.append(value)


class StackInterpreterError(ValueError):
    """Raised when an operation cannot be performed due to underflow or invalid state."""
    pass


def parse_input(lines: List[str]) -> Tuple[Dict[str, int], list]:
    """Parse input into instruction names with line numbers and labels."""
    instructions = []  # Each element is (line_num: int, instruction_name: str)
    labels = {}        # Maps label_name to first_line_idx it can jump to

    idx = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        
        parts = stripped.split()
        
        try:
            while len(parts) > 1 and (parts[0].isdigit() or parts[0] in "UPPER_CASE_LABELS"):
                idx += 1
                parts = [p for p in parts if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", p)]
            
            instructions.append((idx, instr_name))
        except Exception as e:
            raise ValueError(f"Invalid instruction on line {idx}: {e}")

    return instructions, labels
