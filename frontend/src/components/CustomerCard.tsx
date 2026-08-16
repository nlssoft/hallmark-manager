function CustomerCard({ customer }) {
    return (
        <div className="">
            {customer.map((c) => (
                <div key={c.id} className="gap-5 rounded bg-white p-4 shadow">
                    <h3 className="text-lg font-bold">{c.name}</h3>
                    <p className="text-gray-600">{c.address}</p>
                    <p className="text-gray-600">{c.number}</p>
                </div>
            ))}
        </div>
    );
}

export default CustomerCard;
