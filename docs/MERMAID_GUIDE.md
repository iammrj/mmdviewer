# Mermaid Diagram Guide

## What is Mermaid?

Mermaid is a JavaScript-based diagramming tool that renders text-based diagrams into visual charts. Perfect for documentation, flowcharts, and diagrams.

## Supported Diagram Types

### 1. Flowchart
```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
```

### 2. Sequence Diagram
```mermaid
sequenceDiagram
    Alice->>John: Hello John
    John-->>Alice: Hi Alice
```

### 3. Class Diagram
```mermaid
classDiagram
    Animal <|-- Duck
    Animal <|-- Fish
```

### 4. State Diagram
```mermaid
stateDiagram-v2
    [*] --> Still
    Still --> Moving
    Moving --> Still
```

### 5. Gantt Chart
```mermaid
gantt
    title Project Schedule
    section Planning
    Task 1 :a1, 2024-01-01, 30d
```

### 6. Pie Chart
```mermaid
pie title Pets
    "Dogs" : 386
    "Cats" : 85
```

### 7. ER Diagram
```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
```

## Using in the Application

1. **Create** a new file with `.mmd` or `.mermaid` extension
2. **Write** your mermaid diagram code
3. **View** real-time rendering
4. **Export** as:
   - HTML (standalone file)
   - PNG (image)
   - PDF (document)

## Tips

- Use `Ctrl+E` to toggle edit mode
- Changes render automatically after 300ms
- Syntax errors show in the viewer
- Style nodes with CSS-like syntax

## Examples in sample.mmd

Check `sample.mmd` for a working example!
