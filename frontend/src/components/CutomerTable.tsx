import Avatar from "./Avatar";
import MoneyDiv from "./MoneyDiv";


function CustomerTable({customer}){
    

return(
    <div className="w-full overflow-x-auto">
    <table className="w-full min-w-[640px] table-fixed bg-stone-50">
        <thead className="bg-white border border-gray-200 text-gray-600">
            <tr>
                <th className="px-6 py-3 text-left w-1/4">Customer</th>
                <th className="hidden md:table-cell px-6 py-3 text-left w-1/4">Address</th>
                <th className="px-6 py-3 text-left  w-32">Number</th>
                <th className="px-6 py-3 text-left w-28">Due</th>
                <th className="px-6 py-3 text-left w-28">Surplus</th>
            </tr>
        </thead>
        <tbody className="">
                {
                    customer.map((c)=> (
                        <tr key={c.id}
                        className="border-t border-gray-100">
                            <td className="px-6 py-4">
                                <div className="flex items-center gap-3">
                                    <Avatar logo={c.logo}/>
                                    <span className="truncate text-lg ">{c.name}</span>
                                </div>
                            </td>
                        
                            <td className="hidden md:table-cell px-4 py-4 truncate">{c.address}</td>
                            <td className="px-4 py-4">{c.number}</td>
                            <td className="px-6 py-4">
                                <MoneyDiv amount={c.due} color="text-red-500"/> 
                            </td>
                            <td className="px-6 py-4"> 
                                <MoneyDiv amount={c.surplus} color="text-green-700"/>
                            </td>
                            
                        </tr>  
                    ))
                }
        </tbody>
    </table>
    </div>
);
}

export default CustomerTable;