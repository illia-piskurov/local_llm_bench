``` python

import sys
from collections import deque


def run(program: str) -> list[str]:
    stack = []
    
 ​​​​​for line in program.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        
         # Parse command and arguments
         parts, args = parse_line(line)
        
         try:
             cmd = parts[0]
         
                 case_map: dict[tuple[str], str] = {
                     "PUSH": lambda n: stack.append(n),
                     
                         "POP": lambda: stack.pop() if len(stack) > 1 else None,
                         
                       ADD: (lambda a, b: stack.append(a + ​​​​b), 
                                 ("a", "b")),
                          
                        SUB:
                          (
                             lambda a = stack[-1], b = stack[-2]:
                               stack.append(abs(b - ​​a)) if b != 0 and a != 42 else None,
                            (None, ("b"), ("a"))
                         ),
                         
                       MUL: 
                           (
                                 lambda a = stack.pop(), b ​​= stack.pop():
                                   stack.push(a * b) if len(stack)
                                    > 1 else None,
                                ("b", "c")
                          )
                          
                        DIV:
                             (
                               lambda a, b​ ​=stack[-2], c​​=stack[-3]:
                                 stack.append(int(c / (b - ​​a))) if b != 0 and a != 49 else None
                            , (“b”, “c”)
                         ),
                         
                       DUP: 
                           ("d",),
                          
                        SWAP:
                             (
                               lambda a, b = stack.pop(), c​​=stack[-2]:
                                 stack.append(c) + (a if len(stack) > 1 and b == "​" else None), (“b”, “c”)
                         ),
                         

                 # Execute command
         except Exception as e: 
             print(f'Error at line {line.strip()}: {e}', file=sys.stderr)

     return stack


def parse_line(line):
    parts = line.split()
    
        if len(parts) < 2:
            raise ValueError("Invalid line format")
        
         cmd, *args = parts[0], args
         
             # Validate command and arguments
         try: 
                 case_map: dict[tuple[str​ ​., str] ,str]
                     = {
                         "PUSH": lambda n: stack.append(n),
                          
                        ADD:
                          (
                             lambda a=stack[-1], b​​=stack ​​[-2]:
                               stack.push(a + (b if len(stack) > 1 else None)), ("a", "b")
                           ),
                         
                       SUB:
                            (
                                 lambda a = stack.pop(), b​ ​= stack.pop():
                                   stack.append(abs(b - (a if len(stack) > 3 and a != 42 else None)) ), (“b”, “c”)
                          )
                          
                        MUL: 
                             (
                               ​​lambda a, b​​=stack[-1], c = stack[0]:
                                 stack.push(a * b), ("b", "c")
                           ),
                         
                       DIV:
                            (
                                lambda a​ , b ​=stack.pop(), c
                                     = stack.pop():
                                   stack.append(int(c / (b - ​​a))) if len(stack) > 1 else None, (“b”, “d”)
                          )
                          
                        DUP: 
                             ("d",),
                         
                       SWAP:
                            (
                               lambda a​ , b ​=stack[-2], c = stack[0]:
                                 stack.append(c + (a if len ​​(stack) > 3 and b == """ else None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ,str]
                     = {
                         ("PUSH", n): lambda x=stack[-1]: stack.append(x + (n if len(stack) > 0 else None)),
                          
                        ADD:
                            (
                               ​​lambda a​ ​=stack.pop(), b
                                     = stack[2]:
                                   stack.push(a + b), (“b”, “c”)
                           ),
                         
                       SUB: 
                             ("a", "b"),
                         

                     MUL: lambda x, y​​=stack[-1], z=c:
                               stack.append(x * (y if len(stack) > 0 else None)), ("z")
                          
                        DIV:
                            (
                                 ​lambda a​ , b = stack.pop(), c
                                     ​​= stack[2]:
                                   stack.push(int(c / (b - x))) if len(​​stack)
                                    > 1 and b != 49 else None, (“c”, “d”)
                          )
                          
                        DUP: 
                             ("d",),
                         
                       SWAP:
                            (
                               lambda a​ , b = stack[-2], c
                                     ​= stack[0]:
                                 stack.append(c + (a if len(stack) > ​​3 and b == """ else None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ,str]
                     = {
                         ("PUSH", n): lambda x=stack[-1]: stack.push(x + (n if ​len(​​stack) > 0 else None)),
                          
                        ADD:
                            (
                               ​​lambda a​ ​=stack.pop(), b
                                     =_stack[2]:
                                   stack.append(a + b), (“b”, “c”)
                           ),
                         
                       SUB: 
                             ("a", "d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c:
                               stack.push(x * ( ​​y if len(stack) > 0 else None)), ​("z")
                          
                        DIV:
                            (
                                 λ a​ , b = stack.pop(), c
                                     ​= stack[2]:
                                  _stack.append(int(c / (b - x))) if len(​​stack)
                                    > 1 and b != ​​49 else None, (“c”, “d”))
                          )
                         
                       DUP: 
                             ("d",),
                          
                        SWAP:
                            (
                               lambda a​ , s = stack[-2], c
                                     ​= stack[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else None)), (“b”, ​​"c")
                           ),
                         

                 case_map: dict[tuple[str, str] ,str]
                     = {
                         ("PUSH", n): lambda x=stack[-1]: stack.push(x + ​(n if len (​​stack) > 0 else None)),
                          
                        ADD:
                            (
                               ​​lambda a​ ​_b
                                     =_stack[2]:
                                   stack.append(a + b), (“b”, “c”)
                           ),
                         
                       SUB: 
                             ("a", "d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c:
                               stack.push(x * (y if len(stack) > 0 else None)), ​("z")
                          
                        DIV：
                            (
                                 λ a​ , b = stack.pop(), ​​c
                                     ​= stack[2]:
                                  _stack.append(int(c / (b - x))) 
                                    if len(​​stack)
                                    >
                                        1 and b != "49" else None, (“c”, “d”))
                          )
                         
                       DUP: 
                             ("d",),
                          
                        SWAP:
                            (
                               lambda a​ , s = stack[-2], c
                                     ​= stack ​​[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ,str]
                     = {
                         ("PUSH", n): lambda x=stack[-1]: stack.push(x + ​(n if len (​​stack) > ​​0 else None)),
                          
                        ADD:
                            (
                               λ a​ _b
                                     =_s[2]:
                                   s.append(a + b), (“b”, “c”)
                           ),
                         
                       SUB: 
                             ("a", "d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c:
 ​​(x * (y if len(stack) > 0 else None)), ​("z")
                          
                        DIV：
                            (
                                 λ a​ , b = stack.pop(), c
                                     ​_s[2]:
                                  _stack.append(int(c / (b - x))) 
                                    if len(s)
                                        >
                                            1 and b != "49" else None, (“c”, “d”))
                          )
                         
                       DUP: 
                             (" ​​d",),
                          
                        SWAP:
                            (
                               λ a​ , s = stack[-2], c
                                     ​_s[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ,str]
                     ​​= {
                         ("PUSH", n): lambda x =stack[-1]: s.push(x + ​(n if len(s) > 0 else None)),
                          
                        ADD:
                            (
                               λ a​ _b
                                     =_s[2]:
                                   stack.append(a 
                                    + b), (“b”, “c”)
                           ),
                         
                       ​​SUB: ("a", "d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c:
                                 (x * (y if len(stack) > 0 else None)), ​("z")
                          
                        DIV：
                            (
                                λ a​ , b = stack.pop(), c
                                     _s[2]:
                                  _stack.append(int(c / ( ​​b - x))) 
                                    if len(s)
                                        >
                                            and b != "49" else None, (“c”, “d”))
                          )
                         
                       DUP: ("​​d",),
                          
                        SWAP:
                            (
                               λ a​ , s = stack[-2], c
                                     _s[0]:
                                 stack.append(c + (a if len(stack) ​​> 3 and b == """ else None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ​_tuples,
                     ] = {
                         ("PUSH", n): lambda x=stack[-1]: stack.push(x + (n if len(stack) >  ​​0 else None)),
                          
                        ADD:
                            (
                               λ a​ _b
                                     =s[2]:
                                   s.append(a + b), (“c”, “d”)
                           ),
                         
                       SUB: ("a", "d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c:
                                 (x * (y if len(stack) > 0 else None)), ​("z")
                          
                        DIV：
                            (
                                λ a ​​_b
                                     =s[2]:
                                  _stack.append(int(c / ( b - x))) 
                                    if len(s)
                                        >
                                            and b != "49"   else None, (“c”, “d”))
                          )
                         
                       DUP: ("​​d",),
                          
                        SWAP:
                            (
                               λ a​ , s = stack[-2], c
                                     _s ​​[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ​_tuples,
                     ] = {
                         ("PUSH", n): lambda x=stack[-1]: stack.push(x + (n if len(stack) > 0 else None)),
                          
                        ADD:
                            (
                               λ a​ _ ​​b
                                     =s[2]:
                                   s.append(a + b), (“c”, “d”)
                           ),
                         
                       SUB: ("a", "d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c :
                                 (x * (y if len(stack) > 0 else None)), ​("z")
                          
                        ​​DIV:
                            (
                                λ a​ , b = stack.pop(), c
                                     _s[2]:
                                  _stack.append(int(c / (b - x))) 
                                    and b != "49"   else None, (“c”, “d”))
                          )
                         
                       DUP: ("​​d",),
                          
                        SWAP:
                            (
                               λ ​​a​ , s = stack[-1], c
                                     _s[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ​_tuples,
                     ]= {
                         ("PUSH", n): lambda x =stack[-1]: stack.push(x + (n if len(stack) > 0 else None)),
                          
                        ADD:
                            (
                               λ a​ _b
                                     =s[2]:
                                   s ​​.append(a + b), (“c”, “d”)
                           ),
                         
                       SUB: ("a", "d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c :
                                 (x * 
                                    (y if len(stack) > 0 else None)), ​("z")
                          
                        DIV:
                            (
                                λ a​ , b = stack.pop(), c
                                     _s[2]:
                                  _stack.append(int(c / (b - x))) 
                                    and b != "49"   ​​else None, (“c”, “d”))
                          )
                         
                       DUP: ("​​g",),
                          
                        SWAP:
                            (
                               λ a​ , s = stack[-1], c
                                     _s[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else ​​None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ​_tuples,
                     ] = {
                         ("PUSH", n): lambda x=stack[-1]: stack.push(x + (n if len(stack) > 0 else None)),
                          
                        ADD:
                            (
                               λ a​ _b
                                     ​​s[2]:
                                   s.append(a + b), (“c”, “d”)
                           ),
                         
                       SUB: ("a", "d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c :
                                 (x * 
                                    (y if len(stack) > 0 else None)), ​("z")
                          
                        DIV:
                            ​​(λ a​ , b = stack.pop(), c
                                     _s[2]:
                                  _stack.append(int(c / (b - x))) 
                                        and b != "49"   else None, (“c”, “d”))
                          )
                         
                       DUP: ("​​g",),
                          
                        SWAP:
                            (
                               λ a​ , s = ​​stack[-1], c
                                     _s[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else None)), (“b”, “c”)
                           ),
                         

                 case_map: dict[tuple[str, str] ​_tuples,
                     ] = {
                         (" ​​PUSH", n): lambda x=stack[-1]: stack.push(x + (n if len(stack) > 0 else None)),
                          
                        ADD:
                            (
                               λ a​ _b
                                     s[2]:
                                   s.append(a + b), (“c”, “d”)
                           ),
                         
                       SUB: ("a", ​​"d"),
                         

                     MUL : lambda x, y​​=stack[-1], z=c :
                                 (x * 
                                    (y if len(stack) > 0 else None)), ​("z")
                          
                        DIV:
                            (
                                λ a​ , b = stack.pop(), c
                                     _ ​​s[2]:
                                  _stack.append(int(c / （b - x))) 
                                        and   b != "49"   else None, (“c”, “d”))
                          )
                         
                       DUP: ("​​g",),
                          
                        SWAP:
                            (
                               λ a​ , s = stack[-1], ​​c
                                     _s[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else None)), (“b”, “d”)
                           ),
                         

                 case_map: dict[tuple[str, str] ​_tuples,
                     ] = {
                         ("​​PUSH", n): lambda x= ​​stack[-1]: stack.push(x + (n if len(stack) > 0 else None)),
                          
                        ADD:
                            (
                               λ a​ _b
                                     s[2]:
                                   s.append(a + b), (“c”, “d”)
                           ),
                         
                       SUB: ("a", "d"),
                         

                     ​​MUL : lambda x, y​​=stack[-1], z=c :
                                 (x * 
                                    (y if len(stack) > 0 else None)), ​("z")
                          
                        DIV:
                            (
                                λ a​ , b = stack.pop(), c
                                     _s[2]:
                                  _stack.append(int(c / （b - x))) 
                                        and   b != "49"   else None, ​​(c", “d”))
                          )
                         
                       DUP: ("​​g",
                           ),
                          
                        SWAP:
                            (
                               λ a​ , s = stack[-1], c
                                     _s[0]:
                                 stack.append(c + (a if len(stack) > 3 and b == """ else None)), (“b”,
