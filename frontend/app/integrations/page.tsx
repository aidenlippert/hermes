"use client"

import Link from "next/link"
import { Search } from "lucide-react"

const integrations = [
  {
    name: "Slack",
    status: "NEW",
    description: "Send Hermes notifications to Slack channels for real-time collaboration.",
    logo: "https://lh3.googleusercontent.com/aida-public/AB6AXuAmumYQA1teNQeKy0AZ6EVqQfDM4dVCK1MvEnTN375rReoWin5n9MzDrI7XT0WCKw8jpCOs7inTzty6NPYTQKQEkEZ5oU2pTRFVfIfNqR8TfJS4qMaZutrKmSuphv56tj82aInmQZ8oMLD_ycbgxeFiOyNasX99B9paa63nXehshX10VKh7b2nGBtGsBDAvnBs6nOhPotdWQvlIYvgUQv-yCJLRMrjwCGjWkRANi45TuqPrK7mgZioQMqM8xAIOu0BWZSXrmHvc0nk_",
    buttonText: "Connect",
    logoBg: "white",
    logoPadding: true,
  },
  {
    name: "VS Code",
    status: "CONNECTED",
    description: "Integrate agents directly into your development workflow with the Hermes VS Code extension.",
    logo: "https://lh3.googleusercontent.com/aida-public/AB6AXuC6q8185dH4wzcPO1ZUd9cGeNVgsNqa-s6zd36nPtDRr-nNK44_ivXK69GOH3J1x9uhoDs2TlHLx003tYElFRrk_Rj1kfL7f3o7msLU3WkqDRqa6ci3fqPXkmu1ubdIwZIk7u42oUXpscRBWdYkKTyiMf9PRSxgsY5pEgRF3ZyvhgSBJo53JBhvUvoyhqLhXSZx4ZDgkfNNxVBGZtuhbxKTOXDh-9allmnEIdyruAwK93DcLaRC6VdiZjU7m2DHV9G6aqsbzdod-aKy",
    buttonText: "Configure",
  },
  {
    name: "Jira",
    status: "NEW",
    description: "Manage tasks and track project progress by linking Hermes agents to Jira issues.",
    logo: "https://lh3.googleusercontent.com/aida-public/AB6AXuC5c5fHZRYCobX---OBgljAqDv8CwMoGX27W-1PmSaNtxll_7ti-X60gmPRkydSJiwRGl546yHsKoLTr_40qN10Pp7TFVci2whxiXstmuIPC1d2jeubUdmWFSfa2zS7en4rI10NDpxe8hCrSuE_FAD28SVFmMOh-pI4Dvjdu3qyoJCUhzc9G0bsUUlL9twlXQThfsTwOXNDjy-GSmse9MPj2Bhu7AfQg_AjQJg-OhprJPhdafZf5YP5bq8pOfpmaBK8DVDw7VAyjh86",
    buttonText: "Connect",
  },
  {
    name: "Salesforce",
    status: "CONNECTED",
    description: "Sync customer data and automate CRM tasks by connecting Hermes to Salesforce.",
    logo: "https://lh3.googleusercontent.com/aida-public/AB6AXuCTJhk-1U8LmDFjAW3tm42WQHSJpAFky6IaPXs-Mf5DG4npNofisQWE0UJiGiunA7xkifWFr2qvNMFhJkGeMAkLgl4Pbyc1h8ThQiwUsefsqio_yrYa3Vhq_GlixM_mhyUfOunUlKaJHlXo4XGsplQynZM2ilfHE4fpKmMfK1tTlxHyqvtcMH8LAIu7e2ZuLwoXe28cEpyp6e_6TpTm5sSrHe7bGlxFR3GZCny90_VS7-M4RhBy4JQYb2Spe9OCi_2N54wO-hxYJcJm",
    buttonText: "Configure",
  },
  {
    name: "GitHub",
    description: "Automate your code repository tasks, from issue creation to pull request management.",
    logo: "https://lh3.googleusercontent.com/aida-public/AB6AXuD0xe-jbODVrLCtImUUiXFc-0bxX-tmyBCUuTy0gbzVx9rzUQ4hoGLzfdT1xDX4C_jlyp6Hj5wHHIk6OMyWvNATDRL-8B_PKTmZp6euHjqHATQiIsf_fMtUWj0LHlYFrV330q5Hlmtmp7Gfu9293h-8SrY_EKstVEZB50Q7RNNOIM3Jbqu6pXUNSgSAi23ahDGvg2pIvNMfcuRA4mWXDvJiq3CE4liPfuNls6DSl9P_-U8Nu2drmcIDGvaAQxHMAz0IyT4rxUsn8y9c",
    buttonText: "Learn More",
    buttonPrimary: true,
    logoBg: "white",
    logoRounded: true,
  },
  {
    name: "Asana",
    description: "Organize, track, and manage your team's work by integrating with Asana projects.",
    logo: "https://lh3.googleusercontent.com/aida-public/AB6AXuCyM6uC0CCB0Hf9k-34CHsqroW6HmAJtbL-9r19lF7forFVsdXPpMlaFS1t99HM1aR0RJoA6Y7kZXcdPUlqxaLZhTAP85svVl-P2DSmTk7IYueEglxMnmEuimrhXDej7WUJ2v8wBzvgjCtmOd-2_HtVFIoensqT7yALi9Sw3d53rWOzcji6C3TDkROGRPhrc0OWlcXg4TlsrGNp6RX4OEZSuPWR-T3jOi9lE3w5TrrOPqHpD_TWNfN7Qs8BD_tTe2MTjVRYpl8JLanr",
    buttonText: "Connect",
  },
  {
    name: "Notion",
    description: "Connect your knowledge base and documentation for intelligent agent access.",
    logo: "https://lh3.googleusercontent.com/aida-public/AB6AXuA7w75GS2SNTqme_SWp-J-LPgpBZOk74MBQnk4UZiwm4gvfczu4NyXFWk28BdWsIRtaI5CmOzqEpt6Ocue97MRZGMYpG039KP0takMcgN4PslwzrEbMic3-0DYaJAJ7bFXHUN-XfYO4j2RClout2LEdGlPTCBsrML8szcUx8_c_635IcqLJiq1UGrCeZLPpmCuNWIo1FbJcMDzOz4d8eNz_u5yLI7BQQS52dKOf0p6h2N2MQubQ7W_lY_276hMJLT_onEzIcQXgXZvp",
    buttonText: "Connect",
  },
  {
    name: "Google Drive",
    status: "NEW",
    description: "Access and manage documents, spreadsheets, and presentations from Hermes.",
    logo: "https://lh3.googleusercontent.com/aida-public/AB6AXuBF8ngx3lty48d11nZSS8Hiug3T_tgPNZRlzsOvzw09WJ9FW_oMh3QWUg4k3JdpQTEjNCpAQ8JdavPV3_oGoyuE5atCiWCK7xXMTEq8jEQLcPKMdIM56toT1JVJslV7FmZi_gv6A31UyJuEUGYH1oeRkAGXh31-LEKNffKm_Q9aND17sgkCS2NBcCBlLSMzPFjDrA0oM4dEwpd7DhC3CB9dLV2n9FKMtWVe2PrBRdTQUo_pvBcJVgspxwpbcEfU4ympN8Qghpi5HVOe",
    buttonText: "Connect",
  },
];

const FilterChip = ({ label, active = false }: { label: string, active?: boolean }) => (
  <button className={`flex h-10 shrink-0 items-center justify-center gap-x-2 rounded-lg px-4 ${active ? 'bg-primary text-white' : 'bg-[#1e1e1e] hover:bg-white/10 text-gray-300 hover:text-white transition-colors'}`}>
    <p className="text-sm font-medium leading-normal">{label}</p>
  </button>
);

const IntegrationCard = ({ integration }: { integration: typeof integrations[0] }) => (
  <div className="flex flex-col gap-4 p-5 bg-[#1E1E1E] border border-white/10 rounded-xl transition-all hover:border-primary/80 hover:shadow-lg hover:shadow-primary/10">
    <div className="flex items-center gap-4">
      <div 
        className={`size-12 bg-center bg-no-repeat bg-contain rounded-lg ${integration.logoBg ? `bg-${integration.logoBg}` : ''} ${integration.logoPadding ? 'p-1' : ''} ${integration.logoRounded ? 'rounded-full' : ''}`}
        style={{ backgroundImage: `url("${integration.logo}")` }}
      ></div>
      <div className="flex-1">
        <p className="text-white text-lg font-bold leading-normal">{integration.name}</p>
        {integration.status && (
          <span className={`text-xs font-semibold uppercase tracking-wider px-2 py-1 rounded-full ${integration.status === 'NEW' ? 'bg-primary/20 text-primary' : 'bg-green-500/20 text-green-400'}`}>
            {integration.status}
          </span>
        )}
      </div>
    </div>
    <p className="text-gray-400 text-sm font-normal leading-relaxed h-12">{integration.description}</p>
    <button className={`mt-auto w-full flex items-center justify-center h-10 rounded-lg text-sm font-bold transition-colors ${integration.buttonPrimary ? 'bg-primary text-white hover:bg-opacity-80' : 'bg-white/5 text-white hover:bg-white/10'}`}>
      {integration.buttonText}
    </button>
  </div>
);

export default function IntegrationsMarketplacePage() {
  return (
    <div className="relative flex h-auto min-h-screen w-full flex-col font-display bg-background-dark text-white">
      <div className="px-4 sm:px-8 md:px-16 lg:px-24 xl:px-40 flex flex-1 justify-center py-5">
        <div className="flex flex-col w-full max-w-[1280px] flex-1">
          <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-white/10 px-4 py-3">
            <div className="flex items-center gap-4 text-white">
              <div className="size-6 text-primary">
                <svg fill="currentColor" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                  <path d="M13.8261 17.4264C16.7203 18.1174 20.2244 18.5217 24 18.5217C27.7756 18.5217 31.2797 18.1174 34.1739 17.4264C36.9144 16.7722 39.9967 15.2331 41.3563 14.1648L24.8486 40.6391C24.4571 41.267 23.5429 41.267 23.1514 40.6391L6.64374 14.1648C8.00331 15.2331 11.0856 16.7722 13.8261 17.4264Z"></path>
                  <path clipRule="evenodd" d="M39.998 12.236C39.9944 12.2537 39.9875 12.2845 39.9748 12.3294C39.9436 12.4399 39.8949 12.5741 39.8346 12.7175C39.8168 12.7597 39.7989 12.8007 39.7813 12.8398C38.5103 13.7113 35.9788 14.9393 33.7095 15.4811C30.9875 16.131 27.6413 16.5217 24 16.5217C20.3587 16.5217 17.0125 16.131 14.2905 15.4811C12.0012 14.9346 9.44505 13.6897 8.18538 12.8168C8.17384 12.7925 8.16216 12.767 8.15052 12.7408C8.09919 12.6249 8.05721 12.5114 8.02977 12.411C8.00356 12.3152 8.00039 12.2667 8.00004 12.2612C8.00004 12.261 8 12.2607 8.00004 12.2612C8.00004 12.2359 8.0104 11.9233 8.68485 11.3686C9.34546 10.8254 10.4222 10.2469 11.9291 9.72276C14.9242 8.68098 19.1919 8 24 8C28.8081 8 33.0758 8.68098 36.0709 9.72276C37.5778 10.2469 38.6545 10.8254 39.3151 11.3686C39.9006 11.8501 39.9857 12.1489 39.998 12.236ZM4.95178 15.2312L21.4543 41.6973C22.6288 43.5809 25.3712 43.5809 26.5457 41.6973L43.0534 15.223C43.0709 15.1948 43.0878 15.1662 43.104 15.1371L41.3563 14.1648C43.104 15.1371 43.1038 15.1374 43.104 15.1371L43.1051 15.135L43.1065 15.1325L43.1101 15.1261L43.1199 15.1082C43.1276 15.094 43.1377 15.0754 43.1497 15.0527C43.1738 15.0075 43.2062 14.9455 43.244 14.8701C43.319 14.7208 43.4196 14.511 43.5217 14.2683C43.6901 13.8679 44 13.0689 44 12.2609C44 10.5573 43.003 9.22254 41.8558 8.2791C40.6947 7.32427 39.1354 6.55361 37.385 5.94477C33.8654 4.72057 29.133 4 24 4C18.867 4 14.1346 4.72057 10.615 5.94478C8.86463 6.55361 7.30529 7.32428 6.14419 8.27911C4.99695 9.22255 3.99999 10.5573 3.99999 12.2609C3.99999 13.1275 4.29264 13.9078 4.49321 14.3607C4.60375 14.6102 4.71348 14.8196 4.79687 14.9689C4.83898 15.0444 4.87547 15.1065 4.9035 15.1529C4.91754 15.1762 4.92954 15.1957 4.93916 15.2111L4.94662 15.223L4.95178 15.2312ZM35.9868 18.996L24 38.22L12.0131 18.996C12.4661 19.1391 12.9179 19.2658 13.3617 19.3718C16.4281 20.1039 20.0901 20.5217 24 20.5217C27.9099 20.5217 31.5719 20.1039 34.6383 19.3718C35.082 19.2658 35.5339 19.1391 35.9868 18.996Z" fillRule="evenodd"></path>
                </svg>
              </div>
              <h2 className="text-white text-lg font-bold leading-tight tracking-[-0.015em]">Hermes</h2>
            </div>
            <div className="flex flex-1 justify-end items-center gap-6">
              <nav className="hidden md:flex items-center gap-8">
                <Link className="text-gray-400 hover:text-white text-sm font-medium leading-normal transition-colors" href="#">Dashboard</Link>
                <Link className="text-gray-400 hover:text-white text-sm font-medium leading-normal transition-colors" href="#">Agents</Link>
                <Link className="text-white text-sm font-bold leading-normal relative" href="#">Marketplace<span className="absolute -bottom-1 left-0 w-full h-0.5 bg-primary"></span></Link>
              </nav>
              <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuDEv6iAViKWDdhTqyxfzzGNrFcP6Uw1PmvaJVU9kZAzXyU2_indmz37v0P2pvQYtc4pPwUe1vthWLhb5iHsa5cF2MLLvEiMpCEnWP2aRW3kCoa3no-iZOh5N4IzN_12hlbm5wZARs7_crubEMFIu4K6G5IW458LthGCsWWN7VK6l4AZoRHWFwxneGXvBNuDeteyLpF9pWoTCACNMci8a6ygEttO4-txnt2iFmVpxjYPRJwwGvFMgJjK0RYWhOac1-ilRd1hl9HqQ6ZG")' }}></div>
            </div>
          </header>

          <main className="flex-1 mt-8">
            <div className="flex flex-wrap justify-between items-center gap-4 p-4">
              <div className="flex flex-col gap-2">
                <p className="text-white text-4xl font-black leading-tight tracking-[-0.033em]">Integrations Marketplace</p>
                <p className="text-gray-400 text-base font-normal leading-normal">Extend the power of Hermes by connecting your favorite tools and services.</p>
              </div>
            </div>

            <div className="sticky top-0 z-10 bg-background-dark/80 backdrop-blur-sm py-4 px-4">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex-1 min-w-[280px]">
                  <div className="flex w-full flex-1 items-stretch rounded-lg h-12 bg-[#1e1e1e] border border-white/10 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/50 transition-all">
                    <div className="text-gray-400 flex items-center justify-center pl-4">
                      <Search />
                    </div>
                    <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-white focus:outline-0 focus:ring-0 border-none bg-transparent h-full placeholder:text-gray-500 px-4 pl-2 text-base font-normal leading-normal" placeholder="Search integrations..." />
                  </div>
                </div>
                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                  <FilterChip label="All" active />
                  <FilterChip label="Productivity" />
                  <FilterChip label="Developer Tools" />
                  <FilterChip label="CRM" />
                  <FilterChip label="Communication" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-6 p-4 mt-4">
              {integrations.map((integration) => (
                <IntegrationCard key={integration.name} integration={integration} />
              ))}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
