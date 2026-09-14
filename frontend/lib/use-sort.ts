"use client";

import { useCallback, useState } from "react";
import type { SortOrder } from "@/lib/api";

export interface SortState<Field extends string> {
  sortBy: Field;
  order: SortOrder;
  toggle: (field: Field) => void;
  header: { sortBy: Field; order: SortOrder; onSort: (field: Field) => void };
}

export function useSort<Field extends string>(
  initialField: Field,
  initialOrder: SortOrder,
  descendingFirst: readonly Field[],
  onChange?: () => void,
): SortState<Field> {
  const [sortBy, setSortBy] = useState<Field>(initialField);
  const [order, setOrder] = useState<SortOrder>(initialOrder);

  const toggle = useCallback(
    (field: Field) => {
      if (field === sortBy) {
        setOrder((current) => (current === "asc" ? "desc" : "asc"));
      } else {
        setSortBy(field);
        setOrder(descendingFirst.includes(field) ? "desc" : "asc");
      }
      onChange?.();
    },
    [sortBy, descendingFirst, onChange],
  );

  return { sortBy, order, toggle, header: { sortBy, order, onSort: toggle } };
}
