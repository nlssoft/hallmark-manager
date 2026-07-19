import NavBar from "../components/NavBar"
import CustomerTable from "../components/CutomerTable";
const data = [
    {
        id: 1,
        name: "Sharma Jewellers",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 0,
    },
        {
        id: 2,
        name: "Rina Gold House",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 20,
        surplus: 0,
    },
        {
        id: 3,
        name: "Baranagar Ornaments",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 20000,
        surplus: 0,
    },
        {
        id: 4,
        name: "Modern Gold Palace",
        address: "some place far away that I do not no  of like ahfoh shgfoh thoes should be places name in another language.",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 20,
    },
     {
        id:5,
        name: "Kolkata Bullion Co",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 1000,
    }
]

function CustomerPage(){
    return (
        <div className="bg-stone-50">
            <NavBar/>

            <header>
                <title className="bg-red-500">Customers</title>
                <div>
                    <button className="border"> + Add Customer</button>
                </div>
            </header>
            <section>
                <input type="text" className="border" />
            </section>

            <CustomerTable customer={data}/>

            <footer className="mt-20">
                <div>customer count</div>
                <div>pagination</div>
            </footer>
        </div>
    )
}


export default CustomerPage;

