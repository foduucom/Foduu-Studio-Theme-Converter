# Blade-like Syntax in Mustache

This documentation covers the enhanced Blade-like syntax available in your Mustache templates.  
This syntax allows for more expressive conditional logic and loops, similar to Laravel Blade, making templates easier to write and read.

---

## 1. Conditional Logic (`@if`, `@else`)

You can use `@if` directives to conditionally render content.  
It supports standard comparison operators and logical operators.

### Syntax

```mustache
{{ @if(condition) }}
    <!-- Content to show if true -->
{{ @else }}
    <!-- Content to show if false -->
{{ @endif }}
````

### Supported Operators

| Type       | Operators                                      |   |        |
| ---------- | ---------------------------------------------- | - | ------ |
| Comparison | `==`, `===`, `!=`, `!==`, `<`, `>`, `<=`, `>=` |   |        |
| Logical    | `&&` (AND), `                                  |   | ` (OR) |

### Examples

```mustache
<!-- Basic check -->
{{ @if(isLoggedIn) }}
    <p>Welcome back!</p>
{{ @endif }}

<!-- Comparison -->
{{ @if(score > 50) }}
    <p>Pass</p>
{{ @else }}
    <p>Fail</p>
{{ @endif }}

<!-- Complex Logic -->
{{ @if(user.role == 'admin' && user.isActive) }}
    <button>Admin Settings</button>
{{ @endif }}
```

---

## 2. Foreach Loop (`@foreach`)

Iterate over arrays and objects easily.
Supports accessing keys and nested properties.

### Syntax

```mustache
<!-- Array Iteration -->
{{ @foreach(items as item) }}
    {{ item.name }}
{{ @endforeach }}

<!-- Key/Value Iteration -->
{{ @foreach(items as key => item) }}
    {{ key }}: {{ item }}
{{ @endforeach }}
```

### Loop Variable

Inside the loop, a `loop` object is automatically available:

* `loop.index`: Current index (0-based)
* `loop.iteration`: Current iteration (1-based)
* `loop.first`: Boolean, true if first item
* `loop.last`: Boolean, true if last item
* `loop.count`: Total items
* `loop.remaining`: Items remaining

### Example: User List

```mustache
<ul>
{{ @foreach(users as user) }}
    <li>
        {{ loop.iteration }}. {{ user.name }}
        {{ @if(user.isAdmin) }} (Admin) {{ @endif }}
    </li>
{{ @endforeach }}
</ul>
```

---

## 3. For Loop (`@for`)

Standard C-style for loops.
Supports dynamic bounds and optional `$` prefix for variables.

### Syntax

```mustache
{{ @for(init; condition; increment) }}
    <!-- Loop body -->
{{ @endfor }}
```

### Examples

```mustache
<!-- Simple Counter -->
{{ @for(i = 0; i < 5; i++) }}
    Number: {{ i }} <br>
{{ @endfor }}

<!-- Dynamic Bounds (using array length) -->
{{ @for(i = 0; i < users.length; i++) }}
    User Index: {{ i }}
{{ @endfor }}

<!-- With $ prefix (PHP style) -->
{{ @for($k = 1; $k <= 10; $k++) }}
    {{ $k }}
{{ @endfor }}
```

---

## 4. Helpers

### `getByIndex(collection, index)`

Retrieve an item from an array or object using a dynamic index or key.
Useful inside `@for` loops.

#### Example

```mustache
{{ @for(i = 0; i < users.length; i++) }}
    <!-- Access user at index i -->
    Name: {{ getByIndex(users, i).name }}
{{ @endfor }}
```

---

## 5. Nested Examples

You can nest loops and conditions arbitrarily deep.

### Nested Loops

```mustache
{{ @foreach(categories as category) }}
    <h3>{{ category.name }}</h3>
    <ul>
    {{ @foreach(category.products as product) }}
        <li>
            {{ product.name }} - ${{ product.price }}
            {{ @if(product.stock < 5) }}
                <span style="color:red">Low Stock</span>
            {{ @endif }}
        </li>
    {{ @endforeach }}
    </ul>
{{ @endforeach }}
```

---

> **Note:** All variables are accessed relative to the current context.
> Dot notation (e.g., `user.profile.email`) is fully supported in all directives.
