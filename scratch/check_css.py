import sys

def check_braces(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    stack = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for char in line:
            if char == '{':
                stack.append(i + 1)
            elif char == '}':
                if not stack:
                    print(f"Extra closing brace at line {i + 1}")
                else:
                    stack.pop()
    
    if stack:
        for line_num in stack:
            print(f"Unclosed opening brace at line {line_num}")

if __name__ == "__main__":
    check_braces(sys.argv[1])
