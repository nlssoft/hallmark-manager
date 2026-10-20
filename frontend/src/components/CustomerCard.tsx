import useRouting from "../hooks/useRouting";
import MoneyDiv from "./MoneyDiv";

function CustomerCard({ customer }) {
    const nav = useRouting();

    return (
        <div className="flex flex-col gap-4">
            {customer.map((c) => (
                <div
                    key={c.id}
                    onClick={() => nav.customer(c.id)}
                    className="gap-5 rounded-xl bg-white p-4 shadow-md"
                >
                    <h3 className="text-lg font-bold">{c.name}</h3>
                    <div className="flex flex-col gap-3">
                        <div>
                            <p className="text-gray-600">{c.address}</p>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            <MoneyDiv amount={c.due} color="text-red-500" />
                            <MoneyDiv
                                amount={c.surplus}
                                color="text-green-500"
                            />
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default CustomerCard;
