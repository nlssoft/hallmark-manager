import { ChevronLeft, ChevronRight } from "lucide-react";

function Pagination({
    keyWord,
    count,
    page,
}: {
    keyWord: string;
    count: number;
    page: number;
}) {
    const buttonCss =
        "border border-gray-200 rounded-md p-3 bg-white text-gray-700 \
                        hover:text-gray-900  hover:border-amber-200   transition-all duration-100 \
                        shadow-md hover:shadow-lg";

    return (
        <div className="mt-12 mb-4 flex items-center justify-between bg-gray-50 p-4">
            <div className="leading-relaxed font-semibold text-stone-700">
                {`${count} ${keyWord}`}
            </div>

            <div className="flex items-center justify-between gap-3">
                <button className={buttonCss}>
                    <ChevronLeft />
                </button>

                <div className="leading-relaxed text-gray-700 hover:text-gray-900">
                    page {page} of pages
                </div>

                <button className={buttonCss}>
                    <ChevronRight />
                </button>
            </div>
        </div>
    );
}

export default Pagination;
