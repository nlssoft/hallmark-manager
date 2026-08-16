import useRouting from "../hooks/useRouting";
import Avatar from "./Avatar";
import MoneyDiv from "./MoneyDiv";

const tableStyle = {
    thead: "sticky top-[var(--nav-height)] z-10 bg-white border-b-2 border-gray-200 shadow-sm ",
    thWords: "text-left px-6 py-4 text-gray-800",
    thNumbers: "text-right tabular-nums px-6 py-4 text-gray-800",
    td: "px-4 py-3",
    tdNumbers: "px-4 py-3 text-sm tabular-nums text-right",
    row: "border-b border-gray-200 hover:bg-gray-100 hover:border-amber-200 transition-colors duration-200 cursor-pointer odd:bg-white even:bg-stone-50",
};

function CustomerTable({ customer }) {
    const nav = useRouting();

    return (
        <div className="border border-gray-200 bg-white shadow-sm">
            <table className="w-full table-auto">
                <thead className={tableStyle.thead}>
                    <tr>
                        <th className={`${tableStyle.thWords} w-1/4`}>
                            Customer
                        </th>
                        <th className={`${tableStyle.thWords} w-1/4`}>
                            Address
                        </th>
                        <th
                            className={`${tableStyle.thNumbers} hidden text-right md:table-cell`}
                        >
                            Number
                        </th>
                        <th className={`${tableStyle.thNumbers} `}>Due</th>
                        <th className={`${tableStyle.thNumbers} `}>Surplus</th>
                    </tr>
                </thead>
                <tbody>
                    {customer.map((c) => (
                        <tr
                            key={c.id}
                            onClick={() => nav.customer(c.id)}
                            className={tableStyle.row}
                        >
                            <td className={tableStyle.td}>
                                <div className="flex items-center gap-3">
                                    <Avatar logo={c.logo} />
                                    <span className="font-medium text-stone-900">
                                        {c.name}
                                    </span>
                                </div>
                            </td>

                            <td className={`${tableStyle.td}`}>
                                <div className="line-clamp-2 text-sm">
                                    {c.address}
                                </div>
                            </td>
                            <td
                                className={`${tableStyle.tdNumbers} hidden text-gray-800 md:table-cell`}
                            >
                                {c.number}
                            </td>
                            <td
                                className={`${tableStyle.tdNumbers} text-right`}
                            >
                                <MoneyDiv amount={c.due} color="text-red-500" />
                            </td>
                            <td
                                className={`${tableStyle.tdNumbers} text-right`}
                            >
                                <MoneyDiv
                                    amount={c.surplus}
                                    color="text-green-700"
                                />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default CustomerTable;
