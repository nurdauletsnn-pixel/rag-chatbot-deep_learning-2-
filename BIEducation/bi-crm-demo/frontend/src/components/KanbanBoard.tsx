import { DndContext, PointerSensor, useDroppable, useSensor, useSensors, type DragEndEvent } from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { mockBranches, mockChildren, mockParents, mockTariffs } from '../data/mockData'
import type { CurrentUser, Deal, DealStageId, PipelineId } from '../types'
import { pipelineStageOrder, stageLabels } from '../types'
import { DealCard } from './DealCard'

function SortableDealCard({ deal, onSelectDeal }: { deal: Deal; onSelectDeal: (deal: Deal) => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: deal.id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const parent = mockParents.find((entry) => entry.id === deal.parentId)
  const child = mockChildren.find((entry) => entry.id === deal.childId)
  const branch = mockBranches.find((entry) => entry.id === deal.branchId)
  const tariff = mockTariffs.find((entry) => entry.id === deal.tariffId)

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className={isDragging ? 'opacity-60' : ''}>
      <button type="button" onClick={() => onSelectDeal(deal)} className="w-full text-left">
        <DealCard deal={deal} parent={parent ?? null} child={child ?? null} branch={branch ?? null} tariff={tariff ?? null} />
      </button>
    </div>
  )
}

function DroppableColumn({ stage, deals, onSelectDeal }: { stage: DealStageId; deals: Deal[]; onSelectDeal: (deal: Deal) => void }) {
  const { setNodeRef } = useDroppable({ id: stage })

  return (
    <div ref={setNodeRef} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-slate-800">{stageLabels[stage]}</h3>
        <span className="rounded-full bg-white px-2 py-1 text-xs text-slate-500">{deals.length}</span>
      </div>
      <SortableContext items={deals.map((deal) => deal.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-3">
          {deals.map((deal) => (
            <SortableDealCard key={deal.id} deal={deal} onSelectDeal={onSelectDeal} />
          ))}
        </div>
      </SortableContext>
    </div>
  )
}

interface KanbanBoardProps {
  deals: Deal[]
  currentUser: CurrentUser
  pipelineId: PipelineId
  onSelectDeal: (deal: Deal) => void
  onStageChange: (dealId: string, nextStageId: DealStageId) => void
}

export function KanbanBoard({ deals, currentUser, pipelineId, onSelectDeal, onStageChange }: KanbanBoardProps) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || currentUser.role === 'sales_assistant') return

    const deal = deals.find((entry) => entry.id === String(active.id))
    if (!deal) return

    const nextStage = over.id as DealStageId
    onStageChange(deal.id, nextStage)
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="grid gap-4 xl:grid-cols-4 md:grid-cols-2">
        {pipelineStageOrder[pipelineId].map((stage) => {
          const stageDeals = deals.filter((deal) => deal.stageId === stage)

          return <DroppableColumn key={stage} stage={stage} deals={stageDeals} onSelectDeal={onSelectDeal} />
        })}
      </div>
    </DndContext>
  )
}
