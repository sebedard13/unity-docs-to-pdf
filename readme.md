# Issues
1. Link not working in html
2. Links in file not render in pdf
3. Svg may overflow in pdf
4. Code may overflow in pdf

## Maybe solution
### 1
For every page change all tags id to "page-id"+"-id" and now change href from "something.html#else" to "#something-else
### 2
Maybe 1 will help with that
### 3
Transform svg to img and change src to new img
### 4
Transfrom "code" to p with a special class