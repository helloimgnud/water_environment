function TabNavigation({ activeTab, setActiveTab }) {
    const tabs = [
        { id: 'statistics', label: 'Statistics', icon: '' },
        { id: 'calculator', label: 'EAI Calculator', icon: '' },
        { id: 'prediction', label: 'Prediction', icon: '' },
    ];

    return (
        <nav className="tab-navigation">
            {tabs.map((tab) => (
                <button
                    key={tab.id}
                    className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(tab.id)}
                >
                    <span className="tab-icon">{tab.icon}</span>
                    <span className="tab-label">{tab.label}</span>
                </button>
            ))}
        </nav>
    );
}

export default TabNavigation;
