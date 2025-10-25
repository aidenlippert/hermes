"use client"

import { useState } from "react"
import { Link as LinkIcon, Menu, Rocket } from "lucide-react"
import Link from "next/link"

const Switch = ({ checked: initialChecked, label }: { checked: boolean; label: string }) => {
  const [checked, setChecked] = useState(initialChecked)
  return (
    <div className="flex items-center justify-between">
      <span className="text-[#EAEAEA] font-medium">{label}</span>
      <button
        aria-checked={checked}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background-dark ${
          checked ? "bg-primary" : "bg-gray-600"
        }`}
        role="switch"
        type="button"
        onClick={() => setChecked(!checked)}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        ></span>
      </button>
    </div>
  )
}

const RadioGroup = ({ options, name, defaultChecked }: { options: string[]; name: string; defaultChecked: string }) => (
    <div className="space-y-4">
        {options.map((option) => (
            <label key={option} className="flex items-center gap-3 p-3 border border-[#333333] rounded-lg hover:bg-white/5 cursor-pointer">
                <input
                    className="form-radio h-5 w-5 text-primary bg-background-dark border-[#333333] focus:ring-primary"
                    name={name}
                    type="radio"
                    defaultChecked={option === defaultChecked}
                />
                <span className="text-[#EAEAEA]">{option}</span>
            </label>
        ))}
    </div>
)

export default function SubmitAgentPage() {
  return (
    <div className="bg-background-dark font-display text-[#EAEAEA] grid-background-submission">
      <div className="relative flex min-h-screen w-full flex-col">
        <div className="px-4 sm:px-8 md:px-20 lg:px-40 flex flex-1 justify-center py-5">
          <div className="flex flex-col w-full max-w-[960px] flex-1">
            <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#333333] px-4 md:px-10 py-3">
              <div className="flex items-center gap-4">
                <div className="size-6 text-primary">
                  <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M13.8261 17.4264C16.7203 18.1174 20.2244 18.5217 24 18.5217C27.7756 18.5217 31.2797 18.1174 34.1739 17.4264C36.9144 16.7722 39.9967 15.2331 41.3563 14.1648L24.8486 40.6391C24.4571 41.267 23.5429 41.267 23.1514 40.6391L6.64374 14.1648C8.00331 15.2331 11.0856 16.7722 13.8261 17.4264Z"
                      fill="currentColor"
                    ></path>
                    <path
                      clipRule="evenodd"
                      d="M39.998 12.236C39.9944 12.2537 39.9875 12.2845 39.9748 12.3294C39.9436 12.4399 39.8949 12.5741 39.8346 12.7175C39.8168 12.7597 39.7989 12.8007 39.7813 12.8398C38.5103 13.7113 35.9788 14.9393 33.7095 15.4811C30.9875 16.131 27.6413 16.5217 24 16.5217C20.3587 16.5217 17.0125 16.131 14.2905 15.4811C12.0012 14.9346 9.44505 13.6897 8.18538 12.8168C8.17384 12.7925 8.16216 12.767 8.15052 12.7408C8.09919 12.6249 8.05721 12.5114 8.02977 12.411C8.00356 12.3152 8.00039 12.2667 8.00004 12.2612C8.00004 12.261 8 12.2607 8.00004 12.2612C8.00004 12.2359 8.0104 11.9233 8.68485 11.3686C9.34546 10.8254 10.4222 10.2469 11.9291 9.72276C14.9242 8.68098 19.1919 8 24 8C28.8081 8 33.0758 8.68098 36.0709 9.72276C37.5778 10.2469 38.6545 10.8254 39.3151 11.3686C39.9006 11.8501 39.9857 12.1489 39.998 12.236ZM4.95178 15.2312L21.4543 41.6973C22.6288 43.5809 25.3712 43.5809 26.5457 41.6973L43.0534 15.223C43.0709 15.1948 43.0878 15.1662 43.104 15.1371L41.3563 14.1648C43.104 15.1371 43.1038 15.1374 43.104 15.1371L43.1051 15.135L43.1065 15.1325L43.1101 15.1261L43.1199 15.1082C43.1276 15.094 43.1377 15.0754 43.1497 15.0527C43.1738 15.0075 43.2062 14.9455 43.244 14.8701C43.319 14.7208 43.4196 14.511 43.5217 14.2683C43.6901 13.8679 44 13.0689 44 12.2609C44 10.5573 43.003 9.22254 41.8558 8.2791C40.6947 7.32427 39.1354 6.55361 37.385 5.94477C33.8654 4.72057 29.133 4 24 4C18.867 4 14.1346 4.72057 10.615 5.94478C8.86463 6.55361 7.30529 7.32428 6.14419 8.27911C4.99695 9.22255 3.99999 10.5573 3.99999 12.2609C3.99999 13.1275 4.29264 13.9078 4.49321 14.3607C4.60375 14.6102 4.71348 14.8196 4.79687 14.9689C4.83898 15.0444 4.87547 15.1065 4.9035 15.1529C4.91754 15.1762 4.92954 15.1957 4.93916 15.2111L4.94662 15.223L4.95178 15.2312ZM35.9868 18.996L24 38.22L12.0131 18.996C12.4661 19.1391 12.9179 19.2658 13.3617 19.3718C16.4281 20.1039 20.0901 20.5217 24 20.5217C27.9099 20.5217 31.5719 20.1039 34.6383 19.3718C35.082 19.2658 35.5339 19.1391 35.9868 18.996Z"
                      fill="currentColor"
                      fillRule="evenodd"
                    ></path>
                  </svg>
                </div>
                <h2 className="text-[#EAEAEA] text-lg font-bold leading-tight tracking-[-0.015em]">Hermes</h2>
              </div>
              <div className="hidden md:flex flex-1 justify-end gap-8">
                <div className="flex items-center gap-9">
                  <Link className="text-[#EAEAEA] text-sm font-medium leading-normal hover:text-primary transition-colors" href="#">
                    Dashboard
                  </Link>
                  <Link className="text-primary text-sm font-medium leading-normal" href="#">
                    Agents
                  </Link>
                  <Link className="text-[#EAEAEA] text-sm font-medium leading-normal hover:text-primary transition-colors" href="#">
                    API Keys
                  </Link>
                  <Link className="text-[#EAEAEA] text-sm font-medium leading-normal hover:text-primary transition-colors" href="#">
                    Documentation
                  </Link>
                </div>
                <div
                  className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10"
                  style={{
                    backgroundImage:
                      'url("https://lh3.googleusercontent.com/aida-public/AB6AXuChWMuDivocC_LVp5MhLmz2bCPQVyxt51wON6o4mPHpXdxrdFNqu705yQNAwP2MibXEQDlmgwsp8LNHeLNv6DJVh4hiZYguEpald2zfgfj_oPYdRaNpUXQihAU08lk1i2bD3KUth_cX6yZNuwWhouocAjSuFaQjMDqap17Xcz-hEv7QI4gKb3OeKQqifhZb3gfth85KNVilNgEg9v1bWHdoZxUDmv7JiNMdqb_PU0FA6nF1vY_X0ChgiPPYTndoA1T3ebHrz6QlIftJ")',
                  }}
                ></div>
              </div>
              <button className="md:hidden text-white">
                <Menu />
              </button>
            </header>
            <main className="flex-1 mt-8">
              <div className="flex flex-wrap justify-between gap-3 p-4">
                <h1 className="text-[#EAEAEA] text-4xl font-black leading-tight tracking-[-0.033em] min-w-72">
                  Submit New Agent
                </h1>
              </div>
              <div className="space-y-8 p-4">
                <section className="border border-[#333333] rounded-lg">
                  <h2 className="text-[#EAEAEA] text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5 border-b border-[#333333]">
                    Agent Metadata
                  </h2>
                  <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <label className="flex flex-col">
                      <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Agent Name</p>
                      <input
                        className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#EAEAEA] focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-[#333333] bg-background-dark/50 h-14 placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal"
                        placeholder="e.g., Image Analysis Bot"
                      />
                    </label>
                    <label className="flex flex-col">
                      <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Repository URL</p>
                      <div className="relative flex items-center">
                        <input
                          className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#EAEAEA] focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-[#333333] bg-background-dark/50 h-14 placeholder:text-gray-500 p-[15px] pl-10 text-base font-normal leading-normal"
                          placeholder="github.com/user/agent-repo"
                        />
                        <LinkIcon className="text-gray-400 absolute left-3" />
                        <div
                          className="absolute right-3 w-2.5 h-2.5 rounded-full bg-yellow-400"
                          title="Pending validation"
                        ></div>
                      </div>
                    </label>
                    <label className="flex flex-col md:col-span-2">
                      <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Description</p>
                      <textarea
                        className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#EAEAEA] focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-[#333333] bg-background-dark/50 min-h-36 placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal"
                        placeholder="Processes images to identify objects and returns structured data."
                      ></textarea>
                    </label>
                  </div>
                </section>
                <section className="border border-[#333333] rounded-lg">
                  <h2 className="text-[#EAEAEA] text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5 border-b border-[#333333]">
                    Capabilities &amp; Configuration
                  </h2>
                  <div className="p-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
                    <Switch label="File I/O" checked={true} />
                    <Switch label="Network Access" checked={false} />
                    <Switch label="Data Processing" checked={true} />
                    <Switch label="Database Access" checked={false} />
                    <Switch label="External API Calls" checked={true} />
                    <Switch label="User Interface" checked={false} />
                  </div>
                </section>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <section className="border border-[#333333] rounded-lg">
                    <h2 className="text-[#EAEAEA] text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5 border-b border-[#333333]">
                      Pricing Model
                    </h2>
                    <div className="p-4">
                        <RadioGroup name="pricing" options={["Free Tier", "Pay-per-call", "Subscription"]} defaultChecked="Pay-per-call" />
                    </div>
                  </section>
                  <section className="border border-[#333333] rounded-lg">
                    <h2 className="text-[#EAEAEA] text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5 border-b border-[#333333]">
                      Version Management
                    </h2>
                    <div className="p-4 space-y-6">
                      <label className="flex flex-col">
                        <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Version Number</p>
                        <input
                          className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#EAEAEA] focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-[#333333] bg-background-dark/50 h-14 placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal"
                          placeholder="e.g., 1.0.0"
                          defaultValue="1.0.0"
                        />
                      </label>
                      <label className="flex flex-col">
                        <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Release Notes</p>
                        <textarea
                          className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#EAEAEA] focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-[#333333] bg-background-dark/50 min-h-[90px] placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal"
                          placeholder="Initial release with core functionality."
                        ></textarea>
                      </label>
                    </div>
                  </section>
                </div>
              </div>
              <div className="mt-8 p-4 border-t border-[#333333] flex items-center justify-end gap-4">
                <button className="px-6 py-3 rounded-lg text-[#EAEAEA] font-bold text-sm bg-gray-700 hover:bg-gray-600 transition-colors">
                  Save as Draft
                </button>
                <button className="px-8 py-3 rounded-lg text-white font-bold text-sm bg-primary hover:bg-primary/90 transition-colors flex items-center gap-2">
                  <Rocket className="text-lg" />
                  Submit Agent
                </button>
              </div>
            </main>
          </div>
        </div>
      </div>
    </div>
  )
}