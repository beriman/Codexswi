/**
 * Wallet Balance Display & Toggle
 */

document.addEventListener('DOMContentLoaded', () => {
  const walletContainer = document.querySelector('.wallet-balance-container');
  
  if (!walletContainer) {
    return;
  }

  const toggleBtn = walletContainer.querySelector('.wallet-toggle-btn');
  const balanceLink = walletContainer.querySelector('.wallet-balance');
  const balanceAmount = walletContainer.querySelector('.wallet-amount');

  // Load visibility preference from localStorage
  const isVisible = localStorage.getItem('walletBalanceVisible') !== 'false';
  updateVisibility(isVisible);

  // Toggle visibility on button click
  if (toggleBtn) {
    toggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const currentlyVisible = walletContainer.dataset.walletVisible === 'true';
      const newVisible = !currentlyVisible;
      
      localStorage.setItem('walletBalanceVisible', newVisible.toString());
      updateVisibility(newVisible);
    });
  }

  // Fetch and update wallet balance
  fetchWalletBalance();

  // Auto-refresh balance every 30 seconds
  setInterval(fetchWalletBalance, 30000);

  function updateVisibility(visible) {
    walletContainer.dataset.walletVisible = visible.toString();
    
    if (visible) {
      balanceLink.style.display = 'flex';
      toggleBtn.title = 'Sembunyikan saldo';
    } else {
      balanceLink.style.display = 'none';
      toggleBtn.title = 'Tampilkan saldo';
    }
  }

  async function fetchWalletBalance() {
    try {
      const response = await fetch('/api/wallet/balance');
      
      if (!response.ok) {
        console.error('Failed to fetch wallet balance:', response.statusText);
        return;
      }

      const data = await response.json();
      
      if (data.balance !== undefined) {
        const balance = parseFloat(data.balance);
        balanceAmount.dataset.balance = balance;
        balanceAmount.textContent = formatCurrency(balance);
      }
    } catch (error) {
      console.error('Error fetching wallet balance:', error);
    }
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }
});
