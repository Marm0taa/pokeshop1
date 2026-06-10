// ── Cart sidebar toggle ────────────────────────────────────
function toggleCart() {
  document.getElementById('cartSidebar').classList.toggle('open');
  document.getElementById('cartOverlay').classList.toggle('open');
}

// ── Update count badge ─────────────────────────────────────
function updateCartCount(count) {
  document.getElementById('cartCount').textContent = count;
}

// ── Load cart from server ──────────────────────────────────
async function loadCart() {
  const res  = await fetch('/api/cart');
  const data = await res.json();
  renderCartSidebar(data.items, data.total);
  updateCartCount(data.count);
}

// ── Render sidebar items ───────────────────────────────────
function renderCartSidebar(items, total) {
  const container = document.getElementById('cartItems');
  const footer    = document.getElementById('cartFooter');

  if (!items || !items.length) {
    container.innerHTML = '<p class="cart-empty">Tu carrito está vacío 😢</p>';
    footer.style.display = 'none';
    return;
  }

  container.innerHTML = items.map(item => `
    <div class="cart-row">
      <img src="${item.image}" alt="${item.name}" class="cart-row-img">
      <div class="cart-row-info">
        <strong>${item.name}</strong>
        <span>S/ ${item.price}.00 × 
          <input type="number" min="1" max="99" value="${item.qty}"
            style="width:44px;background:transparent;border:1px solid var(--border);color:var(--text);border-radius:4px;padding:2px 4px;font-size:.8rem;"
            onchange="updateQty('${item.id}', this.value)">
        </span>
      </div>
      <span class="cart-row-price">S/ ${(parseFloat(item.price) * item.qty).toFixed(2)}</span>
      <button class="cart-row-remove" onclick="removeFromCart('${item.id}')" title="Quitar">✕</button>
    </div>
  `).join('');

  document.getElementById('cartTotal').textContent = `S/ ${parseFloat(total).toFixed(2)}`;
  footer.style.display = 'block';
}

// ── Remove item ────────────────────────────────────────────
async function removeFromCart(id) {
  const res  = await fetch('/api/cart/remove', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ id })
  });
  const data = await res.json();
  updateCartCount(data.count);
  loadCart();
}

// ── Update qty ─────────────────────────────────────────────
async function updateQty(id, qty) {
  await fetch('/api/cart/update', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ id, qty: parseInt(qty) })
  });
  loadCart();
}

// ── Clear cart ─────────────────────────────────────────────
async function clearCart() {
  await fetch('/api/cart/clear', { method: 'POST' });
  loadCart();
}

// ── Toast notification ─────────────────────────────────────
function showToast(msg) {
  let t = document.querySelector('.toast');
  if (!t) {
    t = document.createElement('div');
    t.className = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2800);
}

// ── Init ───────────────────────────────────────────────────
loadCart();
