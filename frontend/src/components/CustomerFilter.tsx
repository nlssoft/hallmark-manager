import { Search } from "lucide-react";

function CustomerFilter() {
    return (
        <div className="mb-6 flex flex-col gap-3 px-6 py-8 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative w-full sm:flex-1">
                <Search
                    size={18}
                    className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400"
                />

                <input
                    type="search"
                    placeholder="Search by name or logo"
                    className="h-11 w-full rounded-md border border-gray-300 bg-white pl-10 focus:border-blue-500 focus:ring-1 focus:ring-blue-200 focus:outline-none"
                />
            </div>

            <select className="h-11 w-full rounded-md border border-gray-300 bg-white px-3 focus:border-blue-500 focus:ring-1 focus:ring-blue-200 focus:outline-none sm:w-72">
                <option>Sort: Name (A-Z)</option>
                <option>Sort: Name (Z-A)</option>
                <option>Sort: Due (High-Low)</option>
                <option>Sort: Due (Low-High)</option>
            </select>
        </div>
    );
}

export default CustomerFilter;
