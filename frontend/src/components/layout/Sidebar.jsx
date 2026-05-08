import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Camera, MessageSquare, BarChart2, Settings, LogOut } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import Logo from '../ui/Logo'

const NAV_ITEMS = [
  { to: '/dashboard',            icon: LayoutDashboard, label: 'Dashboard'        },
  { to: '/dashboard/screenshot', icon: Camera,          label: 'Verify Screenshot' },
  { to: '/dashboard/sms',        icon: MessageSquare,   label: 'Verify SMS'       },
  { to: '/dashboard/reports',    icon: BarChart2,       label: 'Reports'          },
  { to: '/dashboard/settings',   icon: Settings,        label: 'Settings'         },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <aside className="fixed top-0 left-0 h-screen w-60 bg-slate-900 flex flex-col z-30">
      {/* Brand */}
      <div className="px-5 py-6 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <Logo size={32} dark />
          <span className="text-white font-extrabold text-base tracking-tight">TransferNet</span>
        </div>
      </div>



      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/dashboard'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-white/10 text-white border-l-2 border-blue-400 pl-[10px]'
                  : 'text-white/60 hover:text-white hover:bg-white/[0.05]'
              }`
            }
          >
            <Icon size={16} strokeWidth={2} className="shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
              {/* User badge */}
      <div className="px-5 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white text-sm font-bold shrink-0">
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="min-w-0">
            <p className="text-white text-sm font-semibold truncate leading-tight">{user?.name || 'User'}</p>
            <p className="text-white/40 text-xs truncate">{user?.business_name || ''}</p>
          </div>
        </div>
      </div>
      {/* Sign out */}
      <div className="px-3 py-4 border-t border-white/[0.06]">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white hover:bg-white/[0.05] transition-all duration-150"
        >
          <LogOut size={16} strokeWidth={2} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
