import { Minus } from "lucide-react";

function MoneyDiv({ amount, color }: { amount: number, color: string }) {
    if (amount > 0) {
        return (
            <span className={`text-sm ${color}`}>
                ₹{amount}
            </span>
        );
    }

    return (
        <Minus className="text-gray-300" />
    );
}

export default MoneyDiv;