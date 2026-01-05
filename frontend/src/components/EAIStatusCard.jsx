function EAIStatusCard({ averageEAI, statusDistribution }) {
    const getStatus = (eai) => {
        if (eai === null || eai === undefined) return { status: 'unknown', label: 'N/A', labelVi: 'Không xác định' };
        if (eai >= 80) return { status: 'good', label: 'Good', labelVi: 'Tốt' };
        if (eai >= 50) return { status: 'warning', label: 'Warning', labelVi: 'Cảnh cáo' };
        return { status: 'bad', label: 'Bad', labelVi: 'Xấu' };
    };

    const { status, label, labelVi } = getStatus(averageEAI);
    const total = (statusDistribution.good || 0) +
        (statusDistribution.warning || 0) +
        (statusDistribution.bad || 0) +
        (statusDistribution.unknown || 0);

    return (
        <div className="eai-main-card">
            <h2 style={{ marginBottom: '1rem', color: '#94a3b8' }}>
                Average Environmental Alert Index
            </h2>
            <div className={`eai-score ${status}`}>
                {averageEAI !== null ? averageEAI.toFixed(1) : 'N/A'}
            </div>
            <div className={`eai-status ${status}`}>
                {labelVi} ({label})
            </div>
            <div style={{ marginTop: '1.5rem', color: '#94a3b8' }}>
                Based on {total.toLocaleString()} samples
            </div>
        </div>
    );
}

export default EAIStatusCard;
