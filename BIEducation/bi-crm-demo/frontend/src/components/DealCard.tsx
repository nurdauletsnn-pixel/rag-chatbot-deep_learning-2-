import { AlertTriangle, CarFront, Clock3, Sparkles } from 'lucide-react'
import type { Branch, Child, Deal, Parent, Tariff } from '../types'

interface DealCardProps {
  deal: Deal
  parent: Parent | null
  child: Child | null
  branch: Branch | null
  tariff: Tariff | null
}

export function DealCard({ deal, parent, child, branch, tariff }: DealCardProps) {
  const overdue = deal.tasks.some((task) => !task.isDone && new Date(task.dueDate) < new Date())

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-slate-900">{parent?.name ?? 'Unknown parent'}</p>
          <p className="text-sm text-slate-500">{child?.name ?? 'No child'} • {child?.gradeOrGroup ?? '—'}</p>
        </div>
        <div className="flex flex-wrap justify-end gap-1">
          {deal.addons.transport ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-700">
              <CarFront size={12} /> Transport
            </span>
          ) : null}
          {deal.isWaitlisted ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-2 py-1 text-xs font-medium text-sky-700">
              <Clock3 size={12} /> Waitlist
            </span>
          ) : null}
          {overdue ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-1 text-xs font-medium text-rose-700">
              <AlertTriangle size={12} /> Overdue
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">{branch?.name ?? 'Unknown branch'}</span>
        <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">{tariff?.name ?? 'No tariff'}</span>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
        <span>{deal.addons.food ? 'Food included' : 'No food'}</span>
        <span className="font-semibold text-slate-900">{deal.expectedRevenue.toLocaleString('ru-RU')} ₸</span>
      </div>

      <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
        <Sparkles size={12} />
        <span>{deal.tasks.length} follow-ups</span>
      </div>
    </div>
  )
}
