import CustomerCard from "./CustomerCard";
import CustomerTable from "./CutomerTable";

function CustomerMain({ customer }) {
    return (
        <div>
            <div className="md:hidden">
                <CustomerCard customer={customer} />
            </div>
            <div className="hidden md:block">
                <CustomerTable customer={customer} />
            </div>
        </div>
    );
}

export default CustomerMain;
