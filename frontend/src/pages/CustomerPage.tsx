import NavBar from "../components/NavBar";
import CustomerFilter from "../components/CustomerFilter";
import PageHeader from "../components/PageHeader";
import Pagination from "../components/Pagination";
import CustomerDataView from "../components/CustomerDataView";

const data = [
    {
        id: 1,
        name: "Sharma Jewellers",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 110,
        surplus: 20000,
    },
    {
        id: 2,
        name: "Rina Gold House pvt ltd kashi mandir",
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
        address:
            "some place far away that I do not no  of like ahfoh shgfoh thoes should be places name in another language. regrwethyrtjhtyjh gjoedjlofgf fsdjgloejoe ",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 20,
    },
    {
        id: 5,
        name: "Kolkata Bullion Co",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 1000,
    },
    {
        id: 100,
        name: "Sharma Jewellers",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 0,
    },
    {
        id: 20,
        name: "Rina Gold House",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 20,
        surplus: 0,
    },
    {
        id: 30,
        name: "Baranagar Ornaments",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 20000,
        surplus: 0,
    },
    {
        id: 40,
        name: "Modern Gold Palace",
        address:
            "some place far away that I do not no  of like ahfoh shgfoh thoes should be places name in another language.",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 20,
    },
    {
        id: 10,
        name: "Kolkata Bullion Co",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 1000,
    },
    {
        id: 1000,
        name: "Sharma Jewellers",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 110,
        surplus: 20000,
    },
    {
        id: 2000,
        name: "Rina Gold House",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 20,
        surplus: 0,
    },
    {
        id: 30000,
        name: "Baranagar Ornaments",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 20000,
        surplus: 0,
    },
    {
        id: 40000,
        name: "Modern Gold Palace",
        address:
            "some place far away that I do not no  of like ahfoh shgfoh thoes should be places name in another language.",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 20,
    },
    {
        id: 50000,
        name: "Kolkata Bullion Co",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 1000,
    },
    {
        id: 100000000,
        name: "Sharma Jewellers",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 0,
    },
    {
        id: 200000000,
        name: "Rina Gold House",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 20,
        surplus: 0,
    },
    {
        id: 3000000,
        name: "Baranagar Ornaments",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 20000,
        surplus: 0,
    },
    {
        id: 40000000,
        name: "Modern Gold Palace",
        address:
            "some place far away that I do not no  of like ahfoh shgfoh thoes should be places name in another language.",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 20,
    },
    {
        id: 10000000,
        name: "Kolkata Bullion Co",
        address: "some place",
        number: "123456789",
        logo: "RG",
        due: 0,
        surplus: 1000,
    },
];

function CustomerPage() {
    return (
        <div className="bg-stone-50">
            <NavBar />

            <div className="mx-auto min-h-screen w-full max-w-7xl px-4 py-5 sm:px-5">
                <PageHeader title="Customers" buttonText="Customer" />

                <CustomerFilter />

                <CustomerDataView customer={data} />

                <footer className="mt-8">
                    <Pagination count={20} page={1} keyWord="Customers" />
                </footer>
            </div>
        </div>
    );
}

export default CustomerPage;
