"use client"

import Link from "next/link"
import { Bell, HelpCircle, Download } from "lucide-react"

const statCards = [
  { title: "Current Available Balance", amount: "$1,234.56", color: "text-white" },
  { title: "Pending Payouts", amount: "$300.00", color: "text-primary" },
  { title: "Lifetime Earnings", amount: "$25,890.12", color: "text-white" },
];

const transactions = [
  { date: "Oct 28, 2023", description: "API Usage Earnings - Project X", type: "Earning", amount: "+$150.75", status: "success" },
  { date: "Oct 25, 2023", description: "Monthly Payout", type: "Payout", amount: "-$500.00", status: "payout" },
  { date: "Oct 21, 2023", description: "API Usage Earnings - Project Y", type: "Earning", amount: "+$210.50", status: "success" },
  { date: "Oct 15, 2023", description: "API Usage Earnings - Project X", type: "Earning", amount: "+$139.75", status: "success" },
  { date: "Oct 01, 2023", description: "Payout Attempt Failed", type: "Failed", amount: "-$300.00", status: "failed" },
];

const StatCard = ({ title, amount, color }: { title: string, amount: string, color: string }) => (
  <div className="flex min-w-[158px] flex-1 flex-col gap-2 rounded-lg p-6 bg-[#1E1E1E] border border-white/10">
    <p className="text-white/70 text-base font-medium leading-normal">{title}</p>
    <p className={`tracking-light text-3xl font-bold leading-tight ${color}`}>{amount}</p>
  </div>
);

const TabLink = ({ label, active = false }: { label: string, active?: boolean }) => (
  <Link href="#" className={`flex flex-col items-center justify-center border-b-[3px] pb-[13px] pt-4 ${active ? 'border-b-primary text-white' : 'border-b-transparent text-white/50 hover:text-white/80'}`}>
    <p className="text-sm font-bold leading-normal tracking-[0.015em]">{label}</p>
  </Link>
);

const TransactionRow = ({ date, description, type, amount, status }: typeof transactions[0]) => {
  const statusClasses: { [key: string]: string } = {
    success: "bg-green-500/10 text-green-400",
    payout: "bg-blue-500/10 text-blue-400",
    failed: "bg-red-500/10 text-red-400",
  };
  const amountColor: { [key: string]: string } = {
    success: "text-green-400",
    payout: "text-white/90",
    failed: "text-red-400",
  }

  return (
    <tr className="border-b border-white/10">
      <td className="px-6 py-4">{date}</td>
      <td className="px-6 py-4 font-medium">{description}</td>
      <td className="px-6 py-4">
        <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${statusClasses[status]}`}>
          {type}
        </span>
      </td>
      <td className={`px-6 py-4 text-right font-medium ${amountColor[status]}`}>{amount}</td>
    </tr>
  );
};


export default function BillingPage() {
  return (
    <div className="bg-background-dark font-display text-[#E0E0E0] min-h-screen">
      <div className="px-4 sm:px-8 md:px-12 lg:px-20 xl:px-40 flex flex-1 justify-center py-5">
        <div className="flex flex-col w-full max-w-[960px] flex-1">
          <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-white/10 px-4 sm:px-6 md:px-10 py-3">
            <div className="flex items-center gap-4 text-white">
              <div className="size-6 text-white">
                <svg fill="currentColor" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                  <path d="M13.8261 17.4264C16.7203 18.1174 20.2244 18.5217 24 18.5217C27.7756 18.5217 31.2797 18.1174 34.1739 17.4264C36.9144 16.7722 39.9967 15.2331 41.3563 14.1648L24.8486 40.6391C24.4571 41.267 23.5429 41.267 23.1514 40.6391L6.64374 14.1648C8.00331 15.2331 11.0856 16.7722 13.8261 17.4264Z"></path>
                  <path clipRule="evenodd" d="M39.998 12.236C39.9944 12.2537 39.9875 12.2845 39.9748 12.3294C39.9436 12.4399 39.8949 12.5741 39.8346 12.7175C39.8168 12.7597 39.7989 12.8007 39.7813 12.8398C38.5103 13.7113 35.9788 14.9393 33.7095 15.4811C30.9875 16.131 27.6413 16.5217 24 16.5217C20.3587 16.5217 17.0125 16.131 14.2905 15.4811C12.0012 14.9346 9.44505 13.6897 8.18538 12.8168C8.17384 12.7925 8.16216 12.767 8.15052 12.7408C8.09919 12.6249 8.05721 12.5114 8.02977 12.411C8.00356 12.3152 8.00039 12.2667 8.00004 12.2612C8.00004 12.261 8 12.2607 8.00004 12.2612C8.00004 12.2359 8.0104 11.9233 8.68485 11.3686C9.34546 10.8254 10.4222 10.2469 11.9291 9.72276C14.9242 8.68098 19.1919 8 24 8C28.8081 8 33.0758 8.68098 36.0709 9.72276C37.5778 10.2469 38.6545 10.8254 39.3151 11.3686C39.9006 11.8501 39.9857 12.1489 39.998 12.236ZM4.95178 15.2312L21.4543 41.6973C22.6288 43.5809 25.3712 43.5809 26.5457 41.6973L43.0534 15.223C43.0709 15.1948 43.0878 15.1662 43.104 15.1371L41.3563 14.1648C43.104 15.1371 43.1038 15.1374 43.104 15.1371L43.1051 15.135L43.1065 15.1325L43.1101 15.1261L43.1199 15.1082C43.1276 15.094 43.1377 15.0754 43.1497 15.0527C43.1738 15.0075 43.2062 14.9455 43.244 14.8701C43.319 14.7208 43.4196 14.511 43.5217 14.2683C43.6901 13.8679 44 13.0689 44 12.2609C44 10.5573 43.003 9.22254 41.8558 8.2791C40.6947 7.32427 39.1354 6.55361 37.385 5.94477C33.8654 4.72057 29.133 4 24 4C18.867 4 14.1346 4.72057 10.615 5.94478C8.86463 6.55361 7.30529 7.32428 6.14419 8.27911C4.99695 9.22255 3.99999 10.5573 3.99999 12.2609C3.99999 13.1275 4.29264 13.9078 4.49321 14.3607C4.60375 14.6102 4.71348 14.8196 4.79687 14.9689C4.83898 15.0444 4.87547 15.1065 4.9035 15.1529C4.91754 15.1762 4.92954 15.1957 4.93916 15.2111L4.94662 15.223L4.95178 15.2312ZM35.9868 18.996L24 38.22L12.0131 18.996C12.4661 19.1391 12.9179 19.2658 13.3617 19.3718C16.4281 20.1039 20.0901 20.5217 24 20.5217C27.9099 20.5217 31.5719 20.1039 34.6383 19.3718C35.082 19.2658 35.5339 19.1391 35.9868 18.996Z" fillRule="evenodd"></path>
                </svg>
              </div>
              <h2 className="text-white text-xl font-bold leading-tight tracking-[-0.015em]">Hermes</h2>
            </div>
            <div className="hidden md:flex flex-1 justify-end gap-8">
              <div className="flex items-center gap-9">
                <Link className="text-white/70 hover:text-white text-sm font-medium leading-normal" href="#">Dashboard</Link>
                <Link className="text-white/70 hover:text-white text-sm font-medium leading-normal" href="#">Projects</Link>
                <Link className="text-white/70 hover:text-white text-sm font-medium leading-normal" href="#">API Keys</Link>
                <Link className="text-white text-sm font-bold leading-normal" href="#">Billing & Payouts</Link>
              </div>
              <div className="flex gap-2">
                <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 bg-[#1E1E1E] hover:bg-white/20 text-white gap-2 text-sm font-bold leading-normal tracking-[0.015em] min-w-0 px-2.5">
                  <Bell className="text-white text-xl" />
                </button>
                <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 bg-[#1E1E1E] hover:bg-white/20 text-white gap-2 text-sm font-bold leading-normal tracking-[0.015em] min-w-0 px-2.5">
                  <HelpCircle className="text-white text-xl" />
                </button>
              </div>
              <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBkCnnN5ILooTu3d1H5g9NDW_YkTGTxN57AGJ-NqnON9K1K0YajtbnZKTxqriW3UoEa2ccKe2I0y7zz06VLRTJJYzd8PwLeoVlXGZQ91TUq3C6hpQqD6myC2AzmGUKbyiJ0bAp7SfjY7-qIaEjL4Wq2EurRO-dGJDM-rnDItKpfeeYsHm-pEMMEPeC-zXGKDKFW-CbDZt1JOXr6qs9bCdwL7bOs4rX6KJYMeD-q-Tf9JveIQyEMwrICh28J6uyi52AjWb_I3vWbcOUy")' }}></div>
            </div>
          </header>

          <main className="flex flex-col gap-8 mt-8">
            <div className="flex flex-wrap justify-between gap-3 p-4 items-center">
              <p className="text-white text-4xl font-black leading-tight tracking-[-0.033em] min-w-72">Billing & Payouts</p>
            </div>

            <div className="flex flex-col md:flex-row gap-6 p-4">
              <div className="flex flex-wrap gap-4 flex-1">
                {statCards.map(card => <StatCard key={card.title} {...card} />)}
              </div>
              <div className="flex justify-start items-center">
                <button className="flex min-w-[84px] w-full md:w-auto max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-12 px-6 bg-primary hover:bg-primary/80 text-white text-base font-bold leading-normal tracking-[0.015em]">
                  <span className="truncate">Withdraw Funds</span>
                </button>
              </div>
            </div>

            <div className="pb-3 px-4">
              <div className="flex border-b border-white/10 gap-8">
                <TabLink label="Transaction History" active />
                <TabLink label="Payout Settings" />
                <TabLink label="Invoices" />
              </div>
            </div>

            <div className="flex flex-col gap-4 p-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <input className="bg-[#1E1E1E] border border-white/10 rounded-lg text-white/90 text-sm h-10 px-3 w-64 focus:ring-primary focus:border-primary" placeholder="Filter transactions..." type="text" />
                </div>
                <button className="flex items-center justify-center gap-2 rounded-lg h-10 px-4 bg-[#1E1E1E] border border-white/10 text-white/90 text-sm font-medium hover:bg-white/10">
                  <Download className="w-4 h-4" />
                  <span>Export as CSV</span>
                </button>
              </div>
              <div className="w-full overflow-x-auto rounded-lg bg-[#1E1E1E] border border-white/10">
                <table className="w-full text-left">
                  <thead className="text-xs text-white/50 uppercase border-b border-white/10">
                    <tr>
                      <th className="px-6 py-3 font-medium" scope="col">Date</th>
                      <th className="px-6 py-3 font-medium" scope="col">Description</th>
                      <th className="px-6 py-3 font-medium" scope="col">Type</th>
                      <th className="px-6 py-3 font-medium text-right" scope="col">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm text-white/90">
                    {transactions.map(tx => <TransactionRow key={tx.description + tx.date} {...tx} />)}
                  </tbody>
                </table>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
