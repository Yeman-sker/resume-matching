import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Briefcase, UserSearch, Settings, Workflow } from 'lucide-react'

const navItems = [
  { to: '/', label: '系统监控', icon: LayoutDashboard },
  { to: '/jobs', label: '岗位匹配', icon: Briefcase },
  { to: '/resumes', label: '简历推荐', icon: UserSearch },
  { to: '/generator', label: '生成器控制', icon: Settings },
  { to: '/batch', label: '批处理控制', icon: Workflow },
]

export default function Navbar() {
  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="container mx-auto px-4 h-14 flex items-center justify-between">
        <div className="font-bold text-lg">简历-岗位匹配系统</div>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  )
}