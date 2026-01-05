import { useState } from 'react';

function DataTable({ data }) {
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 20;

    if (!data || data.length === 0) {
        return (
            <div className="data-table-container">
                <h3 style={{ marginBottom: '1rem' }}>Sample Data</h3>
                <p>No data available</p>
            </div>
        );
    }

    const totalPages = Math.ceil(data.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const displayData = data.slice(startIndex, endIndex);

    const goToPage = (page) => {
        if (page >= 1 && page <= totalPages) {
            setCurrentPage(page);
        }
    };

    // Generate page numbers to show
    const getPageNumbers = () => {
        const pages = [];
        const maxVisible = 5;
        let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);

        if (end - start + 1 < maxVisible) {
            start = Math.max(1, end - maxVisible + 1);
        }

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }
        return pages;
    };

    return (
        <div className="data-table-container">
            <div className="table-header">
                <h3>Sample Data</h3>
                <span className="table-info">
                    Showing {startIndex + 1}-{Math.min(endIndex, data.length)} of {data.length} records
                </span>
            </div>

            <table className="data-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Date</th>
                        <th>Region</th>
                        <th>Station</th>
                        <th>Type</th>
                        <th>Layer</th>
                        <th>EAI</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {displayData.map((item, index) => (
                        <tr key={item.id || index}>
                            <td className="row-number">{startIndex + index + 1}</td>
                            <td>{item.date || 'N/A'}</td>
                            <td>{item.region}</td>
                            <td>{item.station}</td>
                            <td>{item.sample_type}</td>
                            <td>{item.water_layer || '-'}</td>
                            <td style={{ fontWeight: 600 }}>
                                {item.eai !== null ? item.eai.toFixed(1) : 'N/A'}
                            </td>
                            <td>
                                <span className={`status-badge ${item.status}`}>
                                    {item.status_label?.vi || item.status}
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* Pagination Controls */}
            {totalPages > 1 && (
                <div className="pagination">
                    <button
                        className="page-btn"
                        onClick={() => goToPage(1)}
                        disabled={currentPage === 1}
                    >
                        First
                    </button>
                    <button
                        className="page-btn"
                        onClick={() => goToPage(currentPage - 1)}
                        disabled={currentPage === 1}
                    >
                        Prev
                    </button>

                    {getPageNumbers().map((page) => (
                        <button
                            key={page}
                            className={`page-btn ${currentPage === page ? 'active' : ''}`}
                            onClick={() => goToPage(page)}
                        >
                            {page}
                        </button>
                    ))}

                    <button
                        className="page-btn"
                        onClick={() => goToPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                    >
                        Next
                    </button>
                    <button
                        className="page-btn"
                        onClick={() => goToPage(totalPages)}
                        disabled={currentPage === totalPages}
                    >
                        Last
                    </button>

                    <span className="page-info">
                        Page {currentPage} of {totalPages}
                    </span>
                </div>
            )}
        </div>
    );
}

export default DataTable;
