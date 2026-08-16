import { useNavigate } from "react-router-dom";

function useRouting() {
    const navigate = useNavigate();

    return {
        dashboard: () => navigate("/dashboard"),

        group(id: string) {
            navigate(`groups/${id}`);
        },

        customer(id: string) {
            navigate(`customers/${id}`);
        },

        service(id: string) {
            navigate(`services/${id}`);
        },

        entries(id: string) {
            navigate(`work-entries/${id}`);
        },

        payment(id: string) {
            navigate(`payments/${id}`);
        },

        audit(id: string) {
            navigate(`audit-logs"/${id}`);
        },

        request(id: string) {
            navigate(`requests/${id}`);
        },

        go(route: string) {
            navigate(route);
        },
    };
}

export default useRouting;
