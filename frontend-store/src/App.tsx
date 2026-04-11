import { useState } from 'react';
import { ShoppingCart, Search, Star, Box, Layers, Shield, Cpu, Database } from 'lucide-react';
import { BLOCKS, CATEGORIES, Block } from './blocks';

function App() {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [cart, setCart] = useState<string[]>([]);
  const [selectedBlock, setSelectedBlock] = useState<Block | null>(null);

  const filteredBlocks = BLOCKS.filter(block => {
    const matchesCategory = selectedCategory === 'All' || block.category === selectedCategory;
    const matchesSearch = block.displayName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         block.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         block.tags.some(t => t.includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const addToCart = (blockName: string) => {
    if (!cart.includes(blockName)) {
      setCart([...cart, blockName]);
    }
  };

  const cartTotal = cart.reduce((sum, name) => {
    const block = BLOCKS.find(b => b.name === name);
    return sum + (block?.price || 0);
  }, 0);

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0f' }}>
      {/* Header */}
      <header style={{ 
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        padding: '20px 40px',
        borderBottom: '1px solid #2a2a3e'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ fontSize: '32px' }}>🧠</div>
            <div>
              <h1 style={{ margin: 0, fontSize: '24px', color: '#fff' }}>Cerebrum Block Store</h1>
              <p style={{ margin: 0, fontSize: '12px', color: '#888' }}>Build AI Like Lego • {BLOCKS.length} Blocks Available</p>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <a href="https://cerebrum-platform.onrender.com" style={{ color: '#6c63ff', textDecoration: 'none', fontSize: '14px' }}>
              Platform Console →
            </a>
            <div style={{ 
              background: '#6c63ff', 
              padding: '10px 20px', 
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: 'white',
              fontWeight: 'bold'
            }}>
              <ShoppingCart size={18} />
              Cart ({cart.length}) - ${cartTotal}/mo
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <div style={{ 
        background: 'linear-gradient(135deg, #6c63ff22, #ff6b3522)',
        padding: '60px 40px',
        textAlign: 'center'
      }}>
        <h2 style={{ fontSize: '36px', color: '#fff', marginBottom: '16px' }}>
          Domain-Specific AI Blocks
        </h2>
        <p style={{ fontSize: '18px', color: '#aaa', maxWidth: '600px', margin: '0 auto' }}>
          One platform. Swappable industries. Pick your vertical and start building.
        </p>
        
        {/* Search */}
        <div style={{ 
          maxWidth: '500px', 
          margin: '30px auto 0',
          position: 'relative'
        }}>
          <Search style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: '#666' }} size={20} />
          <input
            type="text"
            placeholder="Search blocks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '16px 16px 16px 48px',
              borderRadius: '12px',
              border: '1px solid #2a2a3e',
              background: '#1a1a2e',
              color: '#fff',
              fontSize: '16px',
              outline: 'none'
            }}
          />
        </div>
      </div>

      {/* Category Filter */}
      <div style={{ padding: '20px 40px', borderBottom: '1px solid #1e1e2e' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: 'none',
                background: selectedCategory === cat ? '#6c63ff' : '#1a1a2e',
                color: selectedCategory === cat ? '#fff' : '#888',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: selectedCategory === cat ? 'bold' : 'normal'
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Block Grid */}
      <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '24px'
        }}>
          {filteredBlocks.map(block => (
            <div
              key={block.name}
              onClick={() => setSelectedBlock(block)}
              style={{
                background: '#1a1a2e',
                borderRadius: '16px',
                padding: '24px',
                border: '1px solid #2a2a3e',
                cursor: 'pointer',
                transition: 'transform 0.2s, border-color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#6c63ff';
                e.currentTarget.style.transform = 'translateY(-4px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#2a2a3e';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <span style={{ fontSize: '40px' }}>{block.icon}</span>
                <div style={{ 
                  background: block.category === 'Domain' ? '#ff6b35' : '#6c63ff',
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  color: '#fff'
                }}>
                  ${block.price}/mo
                </div>
              </div>
              
              <h3 style={{ margin: '0 0 8px', color: '#fff', fontSize: '20px' }}>{block.displayName}</h3>
              <p style={{ margin: '0 0 16px', color: '#888', fontSize: '14px', lineHeight: '1.5' }}>
                {block.description}
              </p>
              
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '16px' }}>
                {block.tags.map(tag => (
                  <span key={tag} style={{ 
                    background: '#0a0a0f', 
                    padding: '4px 8px', 
                    borderRadius: '4px',
                    fontSize: '11px',
                    color: '#666'
                  }}>
                    {tag}
                  </span>
                ))}
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid #2a2a3e' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#ffd700' }}>
                  <Star size={14} fill="#ffd700" />
                  <span style={{ fontSize: '14px', fontWeight: 'bold' }}>{block.rating}</span>
                  <span style={{ fontSize: '12px', color: '#666' }}>({block.reviews})</span>
                </div>
                <span style={{ fontSize: '12px', color: '#666' }}>by {block.author}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Block Detail Modal */}
      {selectedBlock && (
        <div 
          style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
          }}
          onClick={() => setSelectedBlock(null)}
        >
          <div 
            style={{
              background: '#1a1a2e',
              borderRadius: '20px',
              padding: '40px',
              maxWidth: '500px',
              width: '100%',
              border: '1px solid #2a2a3e'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ fontSize: '60px', marginBottom: '20px' }}>{selectedBlock.icon}</div>
            <h2 style={{ margin: '0 0 12px', color: '#fff', fontSize: '28px' }}>{selectedBlock.displayName}</h2>
            <p style={{ margin: '0 0 20px', color: '#888', fontSize: '16px', lineHeight: '1.6' }}>
              {selectedBlock.description}
            </p>
            
            <div style={{ background: '#0a0a0f', padding: '20px', borderRadius: '12px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ color: '#888' }}>Price</span>
                <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '20px' }}>${selectedBlock.price}/mo</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ color: '#888' }}>Creator Revenue</span>
                <span style={{ color: '#00c853' }}>80%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Platform Fee (Lego Tax)</span>
                <span style={{ color: '#ff6b35' }}>20%</span>
              </div>
            </div>
            
            <button
              onClick={() => {
                addToCart(selectedBlock.name);
                setSelectedBlock(null);
              }}
              style={{
                width: '100%',
                padding: '16px',
                borderRadius: '12px',
                border: 'none',
                background: cart.includes(selectedBlock.name) ? '#2a2a3e' : '#6c63ff',
                color: '#fff',
                fontSize: '16px',
                fontWeight: 'bold',
                cursor: cart.includes(selectedBlock.name) ? 'default' : 'pointer'
              }}
              disabled={cart.includes(selectedBlock.name)}
            >
              {cart.includes(selectedBlock.name) ? '✓ Added to Cart' : 'Add to Cart'}
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer style={{ padding: '40px', textAlign: 'center', borderTop: '1px solid #1e1e2e', color: '#666' }}>
        <p>Cerebrum Blocks • Domain Adapter Protocol v2.0</p>
        <p style={{ fontSize: '12px', marginTop: '8px' }}>
          {BLOCKS.length} Blocks • 8 Domain Containers • 20% Lego Tax
        </p>
      </footer>
    </div>
  );
}

export default App;